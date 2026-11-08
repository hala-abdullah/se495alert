"""Runnable showcase: a Faculty send that is inside their grant (US-3).

Seeds synthetic PSU-shaped data, then walks one allowed send and three denied
ones through the real authorization service. Nothing here is pre-baked output:
every line printed comes from ``authorize_send()`` and ``resolve_recipients()``.

Run with::

    python manage.py demo_faculty_send

The command is idempotent. It only touches accounts and courses whose demo
prefix it created, so it is safe against a database that also holds seeded
demo data (NFR-3: synthetic records only).
"""

from __future__ import annotations

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand

from accounts.models import Profile
from alerts.constants import AudienceType, Severity
from alerts.services.audience import resolve_recipients
from alerts.services.authorization import SendDenied, SendRequest, authorize_send
from audit.models import AuditLogEntry
from courses.models import Course, Enrollment, FacultyAssignment, Section
from directory.models import Department

User = get_user_model()

DEMO_PASSWORD = "demo-only-not-real"
STUDENT_NAMES = ["Noura Demo", "Sami Demo", "Layla Demo", "Omar Demo"]
OTHER_SECTION_STUDENT = "Huda Demo"


class Command(BaseCommand):
    help = "Show one allowed and three denied Faculty alert sends."

    def handle(self, *args, **options):
        data = self._seed()

        self.stdout.write(self.style.MIGRATE_HEADING(
            "\nPSU Alerts -- Faculty authorized-send example"
        ))
        self.stdout.write("=" * 52)
        self._print_cast(data)

        self._allowed_send(data)
        self._denied_send(
            data,
            title="Denied: CRITICAL severity",
            reason="faculty_severity",
            request=SendRequest(
                audience_type=AudienceType.SECTION,
                severity=Severity.CRITICAL,
                section=data["section"],
            ),
        )
        self._denied_send(
            data,
            title="Denied: course they do not teach",
            reason="faculty_course_grant_required",
            request=SendRequest(
                audience_type=AudienceType.COURSE,
                severity=Severity.ADVISORY,
                course=data["ungranted_course"],
            ),
        )
        self._denied_send(
            data,
            title="Denied: campus-wide audience",
            reason="faculty_audience",
            request=SendRequest(
                audience_type=AudienceType.EVERYONE,
                severity=Severity.INFORMATIONAL,
            ),
        )

        self.stdout.write(self.style.MIGRATE_HEADING("\nAudit trail"))
        self.stdout.write("-" * 52)
        entries = AuditLogEntry.objects.filter(
            action__in=[
                AuditLogEntry.Action.SEND_DENIED,
                AuditLogEntry.Action.SEND_OK,
            ]
        ).order_by("created_at", "id")
        for entry in entries:
            self.stdout.write(
                f"  {entry.created_at:%Y-%m-%d %H:%M:%S}  {entry.action:<12}"
                f"  actor={entry.actor_label:<14} reason={entry.detail.get('reason', '-')}"
            )
        self.stdout.write(
            "\nNote: an allowed send is shown as an authorization pass plus a"
            "\nrecipient snapshot. SEND_OK rows arrive with the send pipeline"
            "\n(T3.5); today only denials are written by this service.\n"
        )

    # ------------------------------------------------------------------ seed

    def _seed(self) -> dict:
        dept, _ = Department.objects.get_or_create(
            code="CS", defaults={"name": "Computer Science (synthetic)"}
        )
        course, _ = Course.objects.get_or_create(
            code="CS101",
            defaults={"title": "Introduction to Programming (synthetic)", "department": dept},
        )
        other_course, _ = Course.objects.get_or_create(
            code="CS102",
            defaults={"title": "Data Structures (synthetic)", "department": dept},
        )
        section, _ = Section.objects.get_or_create(
            course=course, code="01", term="2026F"
        )
        other_section, _ = Section.objects.get_or_create(
            course=course, code="02", term="2026F"
        )

        faculty = self._user("demo.faculty", "Demo", "Faculty", Profile.CampusRole.FACULTY)
        self._user(
            "demo.student5",
            "Huda",
            "Demo",
            Profile.CampusRole.STUDENT,
            section=other_section,
        )
        students = [
            self._user(
                f"demo.student{i + 1}",
                name.split()[0],
                name.split()[1],
                Profile.CampusRole.STUDENT,
                section=section,
            )
            for i, name in enumerate(STUDENT_NAMES)
        ]

        FacultyAssignment.objects.get_or_create(
            user=faculty,
            course=course,
            section=None,  # whole-course grant
        )

        return {
            "faculty": faculty,
            "students": students,
            "course": course,
            "section": section,
            "other_section": other_section,
            "ungranted_course": other_course,
        }

    def _user(self, username, first_name, last_name, campus_role, *, section=None):
        user, created = User.objects.get_or_create(
            username=username,
            defaults={"first_name": first_name, "last_name": last_name},
        )
        if created:
            user.set_password(DEMO_PASSWORD)
            user.save(update_fields=["password"])
        Profile.objects.update_or_create(
            user=user,
            defaults={
                "campus_role": campus_role,
                "system_role": Profile.SystemRole.RECIPIENT,
                "synthetic_email": f"{username}@example.edu",
            },
        )
        if section is not None:
            Enrollment.objects.get_or_create(
                user=user,
                section=section,
                defaults={"status": Enrollment.Status.ACTIVE},
            )
        return user

    # --------------------------------------------------------------- report

    def _print_cast(self, data: dict) -> None:
        course = data["course"]
        section = data["section"]
        self.stdout.write("\nSynthetic cast")
        self.stdout.write("-" * 52)
        self.stdout.write(
            f"  demo.faculty  Faculty, grant = whole course {course.code}"
        )
        self.stdout.write(
            f"  {len(data['students'])} students enrolled in {section}"
        )
        self.stdout.write(
            f"  1 student enrolled in {data['other_section']} only"
            "  (must not receive)"
        )

    def _allowed_send(self, data: dict) -> None:
        request = SendRequest(
            audience_type=AudienceType.SECTION,
            severity=Severity.ADVISORY,
            is_urgent=True,
            section=data["section"],
        )
        self.stdout.write(self.style.MIGRATE_HEADING(
            "\nALLOWED -- faculty -> own section, urgent advisory"
        ))
        self.stdout.write("-" * 52)
        self.stdout.write(f"  actor:    {data['faculty'].username}")
        self.stdout.write(
            "  request:  audience=section"
            f" ({data['section']})  severity=ADVISORY  is_urgent=True"
        )

        try:
            authorize_send(data["faculty"], request)
        except SendDenied as exc:  # pragma: no cover - demo must not hit this
            self.stderr.write(self.style.ERROR(f"  unexpectedly denied: {exc.reason}"))
            return

        recipients = resolve_recipients(
            AudienceType.SECTION, section_id=data["section"].pk
        )
        self.stdout.write(self.style.SUCCESS("  decision: allowed (no SEND_DENIED)"))
        self.stdout.write(f"  recipients at send time ({len(recipients)}):")
        for user in recipients:
            self.stdout.write(f"    - {user.username}")
        excluded = [
            u for u in User.objects.filter(username="demo.student5")
            if u not in recipients
        ]
        for user in excluded:
            self.stdout.write(
                f"    x {user.username} (in {data['other_section']}, excluded)"
            )

    def _denied_send(self, data: dict, *, title, reason, request) -> None:
        self.stdout.write(self.style.MIGRATE_HEADING(f"\n{title}"))
        self.stdout.write("-" * 52)
        self.stdout.write(f"  actor:    {data['faculty'].username}")
        self.stdout.write(
            f"  request:  audience={request.audience_type}"
            f"  severity={request.severity}"
            f"  is_urgent={request.is_urgent}"
        )
        try:
            authorize_send(data["faculty"], request)
        except SendDenied as exc:
            ok = exc.reason == reason
            marker = self.style.SUCCESS("denied as expected") if ok else self.style.ERROR(
                f"expected {reason}, got {exc.reason}"
            )
            self.stdout.write(f"  decision: {marker}  reason={exc.reason}")
            entry = AuditLogEntry.objects.filter(
                action=AuditLogEntry.Action.SEND_DENIED,
                detail__reason=exc.reason,
                actor=data["faculty"],
            ).latest("id")
            self.stdout.write(
                f"  audit:    SEND_DENIED #{entry.pk} at"
                f" {entry.created_at:%H:%M:%S}"
            )
        else:  # pragma: no cover - demo must not hit this
            self.stderr.write(self.style.ERROR("  unexpectedly allowed"))
