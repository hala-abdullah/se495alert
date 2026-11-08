"""Audience resolution — selector → recipient snapshot (US-2, AC-2.1–2.4).

Snapshots are written at send time and never re-resolved (NFR-11). A zero-
recipient set is rejected by the caller (AC-2.3).

Every selector is validated before it reaches the ORM. An unknown selector,
wrong target type, or malformed ID resolves to ``[]`` rather than raising: a
bad request must never widen the audience, and a lookup error must never turn
into a 500.
"""

from __future__ import annotations

from django.contrib.auth import get_user_model

from accounts.models import Profile
from courses.models import Enrollment
from directory.models import Building, Department, Group

from ..constants import AudienceType

User = get_user_model()


def resolve_recipients(
    audience_type: str,
    *,
    role: str | None = None,
    department: Department | None = None,
    building: Building | None = None,
    group: Group | None = None,
    course_id: int | None = None,
    section_id: int | None = None,
) -> list[User]:
    """Return a distinct, ordered list of synthetic users at send time."""
    qs = User.objects.filter(is_active=True)

    if audience_type == AudienceType.EVERYONE:
        users = qs.all()
    elif audience_type == AudienceType.ROLE:
        if role not in Profile.CampusRole.values:
            return []
        users = qs.filter(profile__campus_role=role)
    elif audience_type == AudienceType.DEPARTMENT:
        if not _is_saved(department, Department):
            return []
        users = qs.filter(profile__department=department)
    elif audience_type == AudienceType.BUILDING:
        if not _is_saved(building, Building):
            return []
        users = qs.filter(profile__building=building)
    elif audience_type == AudienceType.GROUP:
        if not _is_saved(group, Group):
            return []
        users = group.members.filter(is_active=True)
    elif audience_type == AudienceType.SECTION:
        if not _is_positive_int(section_id):
            return []
        users = User.objects.filter(
            enrollments__section_id=section_id,
            enrollments__status=Enrollment.Status.ACTIVE,
            is_active=True,
        )
    elif audience_type == AudienceType.COURSE:
        if not _is_positive_int(course_id):
            return []
        users = User.objects.filter(
            enrollments__section__course_id=course_id,
            enrollments__status=Enrollment.Status.ACTIVE,
            is_active=True,
        )
    else:
        return []

    # Distinct to avoid duplicate users when a person matches in multiple ways.
    return list(users.distinct().order_by("pk"))


def _is_saved(value, model) -> bool:
    """True only for a saved instance of the expected model."""
    return isinstance(value, model) and value.pk is not None


def _is_positive_int(value) -> bool:
    """True only for a real positive integer, never a bool or numeric string."""
    return isinstance(value, int) and not isinstance(value, bool) and value > 0
