"""Identity and role model (US-9, NFR-21).

A Django ``User`` holds credentials. ``Profile`` holds the PSU-shaped
attributes and the two role axes:

* ``campus_role``  — how the person appears to audience targeting.
* ``system_role``  — what the person may do in the application.

The coarse **role family** (Student / Faculty / Admin) is derived, not stored,
so the stakeholder's three-role language and the finer officer/comms_admin
split can coexist (see docs/reconciliation-2026-11-02.md, D9).
"""

from django.conf import settings
from django.db import models


class RoleFamily(models.TextChoices):
    STUDENT = "STUDENT", "Student"
    FACULTY = "FACULTY", "Faculty"
    ADMIN = "ADMIN", "Admin"


class Profile(models.Model):
    class CampusRole(models.TextChoices):
        STUDENT = "STUDENT", "Student"
        FACULTY = "FACULTY", "Faculty"
        EMPLOYEE = "EMPLOYEE", "Employee"

    class SystemRole(models.TextChoices):
        RECIPIENT = "RECIPIENT", "Recipient"
        OFFICER = "OFFICER", "Alert officer"
        COMMS_ADMIN = "COMMS_ADMIN", "Communications admin"

    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="profile",
    )
    campus_role = models.CharField(
        max_length=16,
        choices=CampusRole.choices,
        default=CampusRole.STUDENT,
    )
    system_role = models.CharField(
        max_length=16,
        choices=SystemRole.choices,
        default=SystemRole.RECIPIENT,
    )
    student_id = models.CharField(
        max_length=32,
        null=True,
        blank=True,
        unique=True,
        help_text="Synthetic PSU-shaped identifier (never a real student number).",
    )
    department = models.ForeignKey(
        "directory.Department",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="members",
    )
    building = models.ForeignKey(
        "directory.Building",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="occupants",
    )
    synthetic_email = models.EmailField(
        blank=True,
        help_text="Must stay on an example.edu-style domain (NFR-3).",
    )
    synthetic_phone = models.CharField(
        max_length=32,
        blank=True,
        help_text="Synthetic only; blank drives the deterministic SMS failure rule.",
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["user__username"]

    @property
    def role_family(self) -> str:
        if self.system_role in (
            self.SystemRole.OFFICER,
            self.SystemRole.COMMS_ADMIN,
        ):
            return RoleFamily.ADMIN
        if self.campus_role == self.CampusRole.FACULTY:
            return RoleFamily.FACULTY
        return RoleFamily.STUDENT

    @property
    def display_name(self) -> str:
        return self.user.get_full_name() or self.user.username

    def __str__(self) -> str:
        return f"{self.user.username} ({self.role_family})"


class OfficerScope(models.Model):
    """An Alert Officer's stored audience grant (US-8, AC-3.1).

    A scope is data, not a hard-coded role: revoking it takes effect on the
    next send attempt (AC-8.2). ``CAMPUS_WIDE`` means every audience selector;
    the other types cover exactly their target (and courses in that
    department for ``DEPARTMENT``).
    """

    class ScopeType(models.TextChoices):
        CAMPUS_WIDE = "CAMPUS_WIDE", "Campus-wide"
        DEPARTMENT = "DEPARTMENT", "Department"
        BUILDING = "BUILDING", "Building"
        GROUP = "GROUP", "Group"

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="officer_scopes",
    )
    scope_type = models.CharField(max_length=16, choices=ScopeType.choices)
    department = models.ForeignKey(
        "directory.Department",
        null=True,
        blank=True,
        on_delete=models.CASCADE,
        related_name="officer_scopes",
    )
    building = models.ForeignKey(
        "directory.Building",
        null=True,
        blank=True,
        on_delete=models.CASCADE,
        related_name="officer_scopes",
    )
    group = models.ForeignKey(
        "directory.Group",
        null=True,
        blank=True,
        on_delete=models.CASCADE,
        related_name="officer_scopes",
    )
    granted_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="officer_scopes_issued",
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["user__username", "scope_type"]
        constraints = [
            models.CheckConstraint(
                condition=(
                    models.Q(
                        scope_type="CAMPUS_WIDE",
                        department__isnull=True,
                        building__isnull=True,
                        group__isnull=True,
                    )
                    | models.Q(
                        scope_type="DEPARTMENT",
                        department__isnull=False,
                        building__isnull=True,
                        group__isnull=True,
                    )
                    | models.Q(
                        scope_type="BUILDING",
                        department__isnull=True,
                        building__isnull=False,
                        group__isnull=True,
                    )
                    | models.Q(
                        scope_type="GROUP",
                        department__isnull=True,
                        building__isnull=True,
                        group__isnull=False,
                    )
                ),
                name="officer_scope_target_matches_type",
            ),
            models.UniqueConstraint(
                fields=["user"],
                condition=models.Q(scope_type="CAMPUS_WIDE"),
                name="uniq_officer_campus_scope",
            ),
            models.UniqueConstraint(
                fields=["user", "department"],
                condition=models.Q(department__isnull=False),
                name="uniq_officer_department_scope",
            ),
            models.UniqueConstraint(
                fields=["user", "building"],
                condition=models.Q(building__isnull=False),
                name="uniq_officer_building_scope",
            ),
            models.UniqueConstraint(
                fields=["user", "group"],
                condition=models.Q(group__isnull=False),
                name="uniq_officer_group_scope",
            ),
        ]

    def __str__(self) -> str:
        target = self.department or self.building or self.group or "campus"
        return f"{self.user.username} → {target}"
