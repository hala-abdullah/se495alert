"""Synthetic courses, sections, enrollments and faculty send grants.

Course/section targeting resolves through enrollments that are active at send
time (AC-14.3). A real SIS import is a handoff concern (A-22); v1 data is
invented.
"""

from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models

from directory.models import Department


class Course(models.Model):
    code = models.CharField(max_length=16, unique=True)
    title = models.CharField(max_length=160)
    department = models.ForeignKey(
        Department,
        on_delete=models.PROTECT,
        related_name="courses",
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["code"]

    def __str__(self) -> str:
        return f"{self.code} — {self.title}"


class Section(models.Model):
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name="sections")
    code = models.CharField(max_length=16)
    term = models.CharField(max_length=16)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["course__code", "code"]
        constraints = [
            models.UniqueConstraint(
                fields=["course", "code", "term"],
                name="uniq_section_per_course_term",
            )
        ]

    def __str__(self) -> str:
        return f"{self.course.code}-{self.code} ({self.term})"


class Enrollment(models.Model):
    class Status(models.TextChoices):
        ACTIVE = "ACTIVE", "Active"
        INACTIVE = "INACTIVE", "Inactive"

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="enrollments",
    )
    section = models.ForeignKey(Section, on_delete=models.CASCADE, related_name="enrollments")
    status = models.CharField(max_length=16, choices=Status.choices, default=Status.ACTIVE)
    enrolled_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["section__course__code", "section__code", "user__username"]
        constraints = [
            models.UniqueConstraint(fields=["user", "section"], name="uniq_enrollment")
        ]
        indexes = [models.Index(fields=["section", "status"])]

    def __str__(self) -> str:
        return f"{self.user.username} → {self.section} ({self.status})"


class FacultyAssignment(models.Model):
    """A faculty member's grant to send to one course or one section.

    ``section`` null means the whole course. A grant never implies a role
    change; it only narrows what the Faculty role may target (AC-3.1, AC-14.1).
    """

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="faculty_assignments",
    )
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name="faculty_assignments")
    section = models.ForeignKey(
        Section,
        null=True,
        blank=True,
        on_delete=models.CASCADE,
        related_name="faculty_assignments",
    )
    granted_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="faculty_grants_issued",
    )
    granted_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["user__username", "course__code"]
        constraints = [
            models.UniqueConstraint(
                fields=["user", "course"],
                condition=models.Q(section__isnull=True),
                name="uniq_faculty_course_grant",
            ),
            models.UniqueConstraint(
                fields=["user", "section"],
                condition=models.Q(section__isnull=False),
                name="uniq_faculty_section_grant",
            ),
        ]

    def clean(self):
        if self.section_id and self.section.course_id != self.course_id:
            raise ValidationError({"section": "Section does not belong to the selected course."})

    def save(self, *args, **kwargs):
        # ``clean()`` is not called automatically. Enforcing it here keeps a
        # mismatched course/section grant out of the database, since the pair
        # cannot be expressed as a single-table CHECK constraint.
        # Bulk operations bypass this; they must not be used for grants.
        self.full_clean()
        return super().save(*args, **kwargs)

    def __str__(self) -> str:
        target = self.section or self.course
        return f"{self.user.username} → {target}"
