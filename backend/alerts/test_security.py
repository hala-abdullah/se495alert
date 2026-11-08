"""Security regression tests for the backend policy and audit boundaries.

P0 set from the backend security test plan:

* S2 — role/scope authorization matrix, precedence, revocation, inactive actor
* S3 — audit integrity, attribution, PII minimisation, fail-safe logging
* S4 — grant/scope database integrity
* S5 — audience snapshot rules (active enrollments, dedupe, no broad fallback)

These exercise the service layer directly. HTTP-boundary tests (IDOR, generic
403 bodies, endpoint permission wiring) arrive with the send endpoint (T3.5).
"""

from __future__ import annotations

import json
import re
from unittest.mock import patch

from django.contrib import admin as django_admin
from django.contrib.auth import get_user_model
from django.contrib.auth.models import AnonymousUser
from django.core.exceptions import ValidationError
from django.db import IntegrityError, transaction
from django.test import TestCase, override_settings

from accounts.models import OfficerScope, Profile
from alerts.constants import AudienceType, Severity
from alerts.services.audience import resolve_recipients
from alerts.services.authorization import SendDenied, SendRequest, authorize_send
from audit.admin import AuditLogEntryAdmin
from audit.models import AuditLogEntry
from audit.writer import log
from courses.models import Course, Enrollment, FacultyAssignment, Section
from directory.models import Building, Department, Group

User = get_user_model()
PASSWORD = "correct-horse-battery"

SEND_DENIED = AuditLogEntry.Action.SEND_DENIED


@override_settings(
    PASSWORD_HASHERS=["django.contrib.auth.hashers.MD5PasswordHasher"]
)
class SecurityFixtures(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.eng = Department.objects.create(code="ENG", name="Engineering")
        cls.med = Department.objects.create(code="MED", name="Medicine")
        cls.science = Building.objects.create(code="SCI", name="Science Hall")
        cls.library = Building.objects.create(code="LIB", name="Library")
        cls.safety = Group.objects.create(code="SAFETY", name="Safety Team")

        cls.cs101 = Course.objects.create(code="CS101", title="Intro CS", department=cls.eng)
        cls.med201 = Course.objects.create(code="MED201", title="Anatomy", department=cls.med)
        cls.cs101_01 = Section.objects.create(course=cls.cs101, code="01", term="2026F")
        cls.cs101_02 = Section.objects.create(course=cls.cs101, code="02", term="2026F")
        cls.empty_section = Section.objects.create(course=cls.cs101, code="99", term="2026F")
        cls.med201_01 = Section.objects.create(course=cls.med201, code="01", term="2026F")

        cls.student = cls._user("sec.student", Profile.CampusRole.STUDENT, cls.eng)
        cls.dual_student = cls._user("sec.dual", Profile.CampusRole.STUDENT, cls.eng)
        cls.inactive_student = cls._user(
            "sec.inactive", Profile.CampusRole.STUDENT, cls.eng, is_active=False
        )
        cls.faculty = cls._user("sec.faculty", Profile.CampusRole.FACULTY, cls.eng)
        cls.section_faculty = cls._user("sec.sectionfac", Profile.CampusRole.FACULTY, cls.eng)
        cls.inactive_faculty = cls._user(
            "sec.inactivefac", Profile.CampusRole.FACULTY, cls.eng, is_active=False
        )
        cls.officer = cls._user(
            "sec.officer", Profile.CampusRole.STUDENT, cls.eng,
            system_role=Profile.SystemRole.OFFICER,
        )
        cls.building_officer = cls._user(
            "sec.buildingofficer", Profile.CampusRole.STUDENT, cls.eng,
            system_role=Profile.SystemRole.OFFICER,
        )
        cls.campus_officer = cls._user(
            "sec.campusofficer", Profile.CampusRole.STUDENT, cls.eng,
            system_role=Profile.SystemRole.OFFICER,
        )
        cls.faculty_officer = cls._user(
            "sec.facultyofficer", Profile.CampusRole.FACULTY, cls.eng,
            system_role=Profile.SystemRole.OFFICER,
        )
        cls.comms = cls._user(
            "sec.comms", Profile.CampusRole.STUDENT, cls.eng,
            system_role=Profile.SystemRole.COMMS_ADMIN,
        )
        cls.employee = cls._user("sec.employee", Profile.CampusRole.EMPLOYEE, cls.eng)
        cls.inactive_enrollee = cls._user(
            "sec.inactiveenrollee", Profile.CampusRole.STUDENT, cls.eng
        )

        cls._enroll(cls.student, cls.cs101_01)
        cls._enroll(cls.dual_student, cls.cs101_01)
        cls._enroll(cls.dual_student, cls.cs101_02)
        cls._enroll(cls.inactive_student, cls.cs101_01)
        cls._enroll(
            cls.inactive_enrollee,
            cls.cs101_01,
            status=Enrollment.Status.INACTIVE,
        )

        # Whole-course grant for one faculty, section-only for another.
        FacultyAssignment.objects.create(user=cls.faculty, course=cls.cs101, section=None)
        FacultyAssignment.objects.create(
            user=cls.inactive_faculty, course=cls.cs101, section=None
        )
        FacultyAssignment.objects.create(
            user=cls.section_faculty, course=cls.cs101, section=cls.cs101_02
        )

        OfficerScope.objects.create(
            user=cls.officer,
            scope_type=OfficerScope.ScopeType.DEPARTMENT,
            department=cls.eng,
        )
        OfficerScope.objects.create(
            user=cls.officer,
            scope_type=OfficerScope.ScopeType.BUILDING,
            building=cls.library,
        )
        OfficerScope.objects.create(
            user=cls.officer,
            scope_type=OfficerScope.ScopeType.GROUP,
            group=cls.safety,
        )
        OfficerScope.objects.create(
            user=cls.building_officer,
            scope_type=OfficerScope.ScopeType.BUILDING,
            building=cls.library,
        )
        OfficerScope.objects.create(
            user=cls.campus_officer,
            scope_type=OfficerScope.ScopeType.CAMPUS_WIDE,
        )

        cls.safety.members.add(cls.student, cls.dual_student)

    @classmethod
    def _user(cls, username, campus_role, department, *, system_role=None, is_active=True):
        user = User.objects.create_user(
            username=username,
            password=PASSWORD,
            first_name="Sec",
            last_name="Test",
            is_active=is_active,
        )
        Profile.objects.create(
            user=user,
            campus_role=campus_role,
            system_role=system_role or Profile.SystemRole.RECIPIENT,
            department=department,
            building=cls.science,
            synthetic_email=f"{username}@example.edu",
        )
        return user

    @classmethod
    def _enroll(cls, user, section, *, status=Enrollment.Status.ACTIVE):
        Enrollment.objects.get_or_create(
            user=user, section=section, defaults={"status": status}
        )

    def denied(self, actor, request, expected_reason):
        with self.assertRaises(SendDenied) as ctx:
            authorize_send(actor, request)
        self.assertEqual(ctx.exception.reason, expected_reason)
        return ctx.exception


class AuthorizationMatrixTests(SecurityFixtures):
    def test_role_severity_audience_matrix(self):
        cases = [
            (
                "student -> section",
                self.student,
                SendRequest(AudienceType.SECTION, Severity.INFORMATIONAL, section=self.cs101_01),
                "role_cannot_send",
            ),
            (
                "student -> everyone",
                self.student,
                SendRequest(AudienceType.EVERYONE, Severity.ADVISORY),
                "role_cannot_send",
            ),
            (
                "employee -> section",
                self.employee,
                SendRequest(AudienceType.SECTION, Severity.ADVISORY, section=self.cs101_01),
                "role_cannot_send",
            ),
            (
                "inactive faculty -> section",
                self.inactive_faculty,
                SendRequest(AudienceType.SECTION, Severity.ADVISORY, section=self.cs101_01),
                "inactive_actor",
            ),
            (
                "faculty -> own section",
                self.faculty,
                SendRequest(AudienceType.SECTION, Severity.ADVISORY, section=self.cs101_01),
                None,
            ),
            (
                "faculty -> own course",
                self.faculty,
                SendRequest(AudienceType.COURSE, Severity.INFORMATIONAL, course=self.cs101),
                None,
            ),
            (
                "faculty -> critical",
                self.faculty,
                SendRequest(AudienceType.SECTION, Severity.CRITICAL, section=self.cs101_01),
                "faculty_severity",
            ),
            (
                "faculty -> everyone",
                self.faculty,
                SendRequest(AudienceType.EVERYONE, Severity.ADVISORY),
                "faculty_audience",
            ),
            (
                "faculty -> unassigned course",
                self.faculty,
                SendRequest(AudienceType.COURSE, Severity.ADVISORY, course=self.med201),
                "faculty_course_grant_required",
            ),
            (
                "faculty+officer follows admin rules",
                self.faculty_officer,
                SendRequest(AudienceType.EVERYONE, Severity.CRITICAL),
                "officer_audience_out_of_scope",
            ),
            (
                "officer -> own department",
                self.officer,
                SendRequest(AudienceType.DEPARTMENT, Severity.CRITICAL, department=self.eng),
                None,
            ),
            (
                "officer -> other department",
                self.officer,
                SendRequest(AudienceType.DEPARTMENT, Severity.ADVISORY, department=self.med),
                "officer_audience_out_of_scope",
            ),
            (
                "officer -> own building",
                self.officer,
                SendRequest(AudienceType.BUILDING, Severity.ADVISORY, building=self.library),
                None,
            ),
            (
                "officer -> own group",
                self.officer,
                SendRequest(AudienceType.GROUP, Severity.ADVISORY, group=self.safety),
                None,
            ),
            (
                "officer -> other department course",
                self.officer,
                SendRequest(AudienceType.COURSE, Severity.ADVISORY, course=self.med201),
                "officer_audience_out_of_scope",
            ),
            (
                "building-only officer -> course",
                self.building_officer,
                SendRequest(AudienceType.COURSE, Severity.ADVISORY, course=self.cs101),
                "officer_audience_out_of_scope",
            ),
            (
                "comms admin -> everyone",
                self.comms,
                SendRequest(AudienceType.EVERYONE, Severity.CRITICAL),
                None,
            ),
            (
                "comms admin -> group",
                self.comms,
                SendRequest(AudienceType.GROUP, Severity.ADVISORY, group=self.safety),
                None,
            ),
            (
                "comms admin -> other course",
                self.comms,
                SendRequest(AudienceType.COURSE, Severity.CRITICAL, course=self.med201),
                None,
            ),
            (
                "anonymous",
                AnonymousUser(),
                SendRequest(AudienceType.SECTION, Severity.ADVISORY, section=self.cs101_01),
                "unauthenticated",
            ),
            (
                "invalid severity",
                self.faculty,
                SendRequest(AudienceType.SECTION, "BOGUS", section=self.cs101_01),
                "invalid_severity",
            ),
            (
                "invalid audience",
                self.faculty,
                SendRequest("bogus", Severity.ADVISORY),
                "invalid_audience",
            ),
        ]

        for label, actor, request, expected in cases:
            with self.subTest(label):
                before = AuditLogEntry.objects.filter(action=SEND_DENIED).count()
                if expected is None:
                    authorize_send(actor, request)
                    self.assertEqual(
                        AuditLogEntry.objects.filter(action=SEND_DENIED).count(), before
                    )
                else:
                    self.denied(actor, request, expected)
                    self.assertEqual(
                        AuditLogEntry.objects.filter(action=SEND_DENIED).count(),
                        before + 1,
                    )

    def test_section_grant_does_not_cross_sections_or_courses(self):
        self.denied(
            self.section_faculty,
            SendRequest(AudienceType.SECTION, Severity.ADVISORY, section=self.cs101_01),
            "faculty_course_grant_required",
        )
        self.denied(
            self.section_faculty,
            SendRequest(AudienceType.SECTION, Severity.ADVISORY, section=self.med201_01),
            "faculty_course_grant_required",
        )
        self.denied(
            self.section_faculty,
            SendRequest(AudienceType.COURSE, Severity.ADVISORY, course=self.cs101),
            "faculty_course_grant_required",
        )

    def test_revoking_a_course_grant_takes_effect_immediately(self):
        request = SendRequest(AudienceType.SECTION, Severity.ADVISORY, section=self.cs101_01)
        authorize_send(self.faculty, request)

        FacultyAssignment.objects.filter(user=self.faculty).delete()

        self.denied(self.faculty, request, "faculty_course_grant_required")

    def test_revoking_an_officer_scope_takes_effect_immediately(self):
        request = SendRequest(
            AudienceType.DEPARTMENT, Severity.ADVISORY, department=self.eng
        )
        authorize_send(self.officer, request)

        OfficerScope.objects.filter(
            user=self.officer, scope_type=OfficerScope.ScopeType.DEPARTMENT
        ).delete()

        self.denied(self.officer, request, "officer_audience_out_of_scope")

    def test_building_scope_does_not_cover_other_selectors(self):
        for request in (
            SendRequest(AudienceType.COURSE, Severity.ADVISORY, course=self.cs101),
            SendRequest(AudienceType.SECTION, Severity.ADVISORY, section=self.cs101_01),
            SendRequest(AudienceType.DEPARTMENT, Severity.ADVISORY, department=self.eng),
            SendRequest(AudienceType.EVERYONE, Severity.ADVISORY),
        ):
            with self.subTest(audience=request.audience_type):
                self.denied(
                    self.building_officer, request, "officer_audience_out_of_scope"
                )

        authorize_send(
            self.building_officer,
            SendRequest(AudienceType.BUILDING, Severity.ADVISORY, building=self.library),
        )

    def test_department_scope_uses_the_sections_actual_course(self):
        authorize_send(
            self.officer,
            SendRequest(AudienceType.SECTION, Severity.ADVISORY, section=self.cs101_01),
        )
        self.denied(
            self.officer,
            SendRequest(AudienceType.SECTION, Severity.ADVISORY, section=self.med201_01),
            "officer_audience_out_of_scope",
        )

    def test_comms_admin_needs_no_stored_scope(self):
        self.assertFalse(OfficerScope.objects.filter(user=self.comms).exists())
        authorize_send(
            self.comms, SendRequest(AudienceType.EVERYONE, Severity.CRITICAL)
        )


class AuditBoundaryTests(SecurityFixtures):
    def _latest_denial(self):
        return AuditLogEntry.objects.filter(action=SEND_DENIED).latest("id")

    def test_each_denial_writes_exactly_one_entry(self):
        before = AuditLogEntry.objects.filter(action=SEND_DENIED).count()
        self.denied(
            self.student,
            SendRequest(AudienceType.EVERYONE, Severity.ADVISORY),
            "role_cannot_send",
        )
        self.assertEqual(
            AuditLogEntry.objects.filter(action=SEND_DENIED).count(), before + 1
        )

        entry = self._latest_denial()
        self.assertEqual(entry.object_type, "alert")
        self.assertEqual(entry.detail["reason"], "role_cannot_send")
        self.assertIn("target_ids", entry.detail)

    def test_denial_is_attributed_to_the_actual_actor(self):
        self.denied(
            self.officer,
            SendRequest(AudienceType.DEPARTMENT, Severity.ADVISORY, department=self.med),
            "officer_audience_out_of_scope",
        )
        entry = self._latest_denial()
        self.assertEqual(entry.actor, self.officer)
        self.assertEqual(entry.actor_label, self.officer.username)
        self.assertEqual(entry.detail["target_ids"]["department"], self.med.pk)

    def test_audit_detail_and_label_contain_no_contact_data(self):
        self.denied(
            self.student,
            SendRequest(AudienceType.SECTION, Severity.ADVISORY, section=self.cs101_01),
            "role_cannot_send",
        )
        entry = self._latest_denial()
        payload = json.dumps(entry.detail)
        self.assertNotIn("@", payload)
        self.assertIsNone(re.search(r"\+?\d{7,}", payload))
        self.assertNotIn("@", entry.actor_label)
        self.assertGreaterEqual(len(payload), 2)

    def test_writer_truncates_untrusted_labels(self):
        entry = log(
            action=SEND_DENIED,
            actor_label="a" * 500,
            object_type="o" * 500,
            object_id="i" * 500,
            detail={"reason": "test"},
        )
        self.assertLessEqual(len(entry.actor_label), 150)
        self.assertLessEqual(len(entry.object_type), 64)
        self.assertLessEqual(len(entry.object_id), 64)

    def test_append_only_admin_has_no_mutation_paths(self):
        model_admin = AuditLogEntryAdmin(AuditLogEntry, django_admin.site)
        self.assertFalse(model_admin.has_add_permission(None))
        self.assertFalse(model_admin.has_change_permission(None))
        self.assertFalse(model_admin.has_delete_permission(None))

        entry = log(action=SEND_DENIED, actor_label="demo")
        entry.object_id = "changed"
        with self.assertRaises(ValueError):
            entry.save()

    def test_audit_failure_does_not_mask_the_denial(self):
        before = AuditLogEntry.objects.filter(action=SEND_DENIED).count()
        with patch(
            "alerts.services.authorization.log",
            side_effect=RuntimeError("audit store unavailable"),
        ):
            self.denied(
                self.student,
                SendRequest(AudienceType.EVERYONE, Severity.ADVISORY),
                "role_cannot_send",
            )
        self.assertEqual(
            AuditLogEntry.objects.filter(action=SEND_DENIED).count(), before
        )


class GrantIntegrityTests(SecurityFixtures):
    def test_department_scope_requires_a_department(self):
        with self.assertRaises(IntegrityError):
            with transaction.atomic():
                OfficerScope.objects.create(
                    user=self.officer,
                    scope_type=OfficerScope.ScopeType.DEPARTMENT,
                )

    def test_duplicate_campus_scope_is_rejected(self):
        with self.assertRaises(IntegrityError):
            with transaction.atomic():
                OfficerScope.objects.create(
                    user=self.campus_officer,
                    scope_type=OfficerScope.ScopeType.CAMPUS_WIDE,
                )

    def test_duplicate_department_scope_is_rejected(self):
        with self.assertRaises(IntegrityError):
            with transaction.atomic():
                OfficerScope.objects.create(
                    user=self.officer,
                    scope_type=OfficerScope.ScopeType.DEPARTMENT,
                    department=self.eng,
                )

    def test_faculty_grant_section_must_belong_to_the_course(self):
        with self.assertRaises(ValidationError):
            FacultyAssignment.objects.create(
                user=self.faculty,
                course=self.cs101,
                section=self.med201_01,
            )

    def test_duplicate_section_code_per_course_term_is_rejected(self):
        with self.assertRaises(IntegrityError):
            with transaction.atomic():
                Section.objects.create(course=self.cs101, code="01", term="2026F")

    def test_duplicate_enrollment_is_rejected(self):
        with self.assertRaises(IntegrityError):
            with transaction.atomic():
                Enrollment.objects.create(user=self.student, section=self.cs101_01)


class AudienceSnapshotTests(SecurityFixtures):
    def test_inactive_enrollment_is_excluded(self):
        recipients = resolve_recipients(
            AudienceType.SECTION, section_id=self.cs101_01.pk
        )
        self.assertNotIn(self.inactive_enrollee, recipients)

    def test_inactive_user_is_excluded(self):
        recipients = resolve_recipients(
            AudienceType.SECTION, section_id=self.cs101_01.pk
        )
        self.assertNotIn(self.inactive_student, recipients)

    def test_duplicate_enrollments_are_deduped(self):
        recipients = resolve_recipients(AudienceType.COURSE, course_id=self.cs101.pk)
        pks = [user.pk for user in recipients]
        self.assertEqual(pks.count(self.dual_student.pk), 1)

    def test_section_course_snapshot_is_distinct_and_ordered(self):
        recipients = resolve_recipients(AudienceType.COURSE, course_id=self.cs101.pk)
        pks = [user.pk for user in recipients]
        self.assertEqual(pks, sorted(pks))
        self.assertEqual(len(pks), len(set(pks)))

    def test_empty_section_resolves_to_zero_recipients(self):
        self.assertEqual(
            resolve_recipients(
                AudienceType.SECTION, section_id=self.empty_section.pk
            ),
            [],
        )

    def test_missing_target_never_falls_back_to_everyone(self):
        self.assertEqual(resolve_recipients(AudienceType.SECTION), [])
        self.assertEqual(resolve_recipients(AudienceType.COURSE), [])
        self.assertEqual(resolve_recipients(AudienceType.DEPARTMENT), [])
        self.assertEqual(resolve_recipients(AudienceType.GROUP), [])

    def test_group_resolution_returns_members_only(self):
        recipients = resolve_recipients(AudienceType.GROUP, group=self.safety)
        self.assertEqual(
            {user.pk for user in recipients},
            {self.student.pk, self.dual_student.pk},
        )

    def test_resolution_is_materialised_at_call_time(self):
        recipients = resolve_recipients(
            AudienceType.SECTION, section_id=self.cs101_01.pk
        )
        self.assertIn(self.student, recipients)

        Enrollment.objects.filter(
            user=self.student, section=self.cs101_01
        ).update(status=Enrollment.Status.INACTIVE)

        # The previously returned list is a snapshot...
        self.assertIn(self.student, recipients)
        # ...but the next resolution reflects the change.
        self.assertNotIn(
            self.student,
            resolve_recipients(AudienceType.SECTION, section_id=self.cs101_01.pk),
        )


class InvalidInputTests(SecurityFixtures):
    """Malformed send requests must be refused cleanly, never crash or widen."""

    def test_comms_admin_cannot_bypass_audience_shape_validation(self):
        cases = [
            SendRequest(AudienceType.DEPARTMENT, Severity.ADVISORY),
            SendRequest(AudienceType.BUILDING, Severity.ADVISORY),
            SendRequest(AudienceType.GROUP, Severity.ADVISORY),
            SendRequest(AudienceType.COURSE, Severity.ADVISORY),
            SendRequest(AudienceType.SECTION, Severity.ADVISORY),
            SendRequest(AudienceType.ROLE, Severity.ADVISORY),
        ]
        for request in cases:
            with self.subTest(audience=request.audience_type):
                self.denied(self.comms, request, "invalid_audience")

    def test_unsaved_target_is_rejected_cleanly(self):
        unsaved_course = Course(code="NEW101", title="Unsaved", department=self.eng)
        self.assertIsNone(unsaved_course.pk)
        self.denied(
            self.comms,
            SendRequest(AudienceType.COURSE, Severity.ADVISORY, course=unsaved_course),
            "invalid_audience",
        )

        unsaved_department = Department(code="NEW", name="Unsaved")
        self.denied(
            self.comms,
            SendRequest(
                AudienceType.DEPARTMENT,
                Severity.ADVISORY,
                department=unsaved_department,
            ),
            "invalid_audience",
        )

    def test_wrong_target_type_is_rejected_cleanly(self):
        cases = [
            SendRequest(AudienceType.DEPARTMENT, Severity.ADVISORY, department=self.cs101),
            SendRequest(AudienceType.BUILDING, Severity.ADVISORY, building=self.safety),
            SendRequest(AudienceType.GROUP, Severity.ADVISORY, group=self.cs101_01),
            SendRequest(AudienceType.COURSE, Severity.ADVISORY, course=self.cs101_01),
            SendRequest(AudienceType.SECTION, Severity.ADVISORY, section=self.cs101),
        ]
        for request in cases:
            with self.subTest(audience=request.audience_type):
                self.denied(self.comms, request, "invalid_audience")

    def test_section_from_a_different_course_is_rejected(self):
        self.denied(
            self.comms,
            SendRequest(
                AudienceType.SECTION,
                Severity.ADVISORY,
                course=self.med201,
                section=self.cs101_01,
            ),
            "invalid_audience",
        )

    def test_non_boolean_urgency_is_rejected(self):
        for value in ("false", "true", 1, 0, None, []):
            with self.subTest(value=repr(value)):
                self.denied(
                    self.comms,
                    SendRequest(
                        AudienceType.EVERYONE,
                        Severity.ADVISORY,
                        is_urgent=value,
                    ),
                    "invalid_urgency",
                )

    def test_unknown_role_value_is_rejected(self):
        self.denied(
            self.comms,
            SendRequest(AudienceType.ROLE, Severity.ADVISORY, role="PRINCIPAL"),
            "invalid_audience",
        )

    def test_valid_role_value_is_allowed(self):
        authorize_send(
            self.comms,
            SendRequest(
                AudienceType.ROLE,
                Severity.ADVISORY,
                role=Profile.CampusRole.STUDENT,
            ),
        )


class AudienceInputTests(SecurityFixtures):
    """The resolver never raises and never broadens on malformed input."""

    def test_malformed_numeric_ids_resolve_to_nothing(self):
        for value in ("abc", "1", -1, 0, 1.5, True, False, None):
            with self.subTest(value=repr(value)):
                self.assertEqual(
                    resolve_recipients(AudienceType.SECTION, section_id=value), []
                )
                self.assertEqual(
                    resolve_recipients(AudienceType.COURSE, course_id=value), []
                )

    def test_wrong_group_or_department_type_resolves_to_nothing(self):
        self.assertEqual(resolve_recipients(AudienceType.GROUP, group="SAFETY"), [])
        self.assertEqual(resolve_recipients(AudienceType.GROUP, group=7), [])
        self.assertEqual(
            resolve_recipients(AudienceType.DEPARTMENT, department=self.cs101), []
        )
        self.assertEqual(
            resolve_recipients(AudienceType.BUILDING, building=self.safety), []
        )

    def test_unknown_role_or_audience_resolves_to_nothing(self):
        self.assertEqual(
            resolve_recipients(AudienceType.ROLE, role="PRINCIPAL"), []
        )
        self.assertEqual(resolve_recipients("bogus"), [])

    def test_unsaved_target_resolves_to_nothing(self):
        unsaved = Department(code="NEW", name="Unsaved")
        self.assertEqual(
            resolve_recipients(AudienceType.DEPARTMENT, department=unsaved), []
        )
