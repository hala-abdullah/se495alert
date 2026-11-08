"""Role and scope authorization for alert sends (US-3, US-8, US-14, NFR-1).

This is the single decision point. Views and serializers must call
``authorize_send()`` and must not re-implement the rules. A denied attempt is
audited here, so a caller cannot forget (AC-3.2, AC-3.8).

Rules
-----
* Any unauthenticated or inactive actor — never sends.
* Student — never sends.
* Faculty — ADVISORY/INFORMATIONAL only, only to an assigned course/section,
  may set ``is_urgent``.
* Officer — any severity, but only within stored ``OfficerScope`` grants.
* Comms admin — any severity, any audience.

A scope/grant is data: revocation takes effect on the next call (AC-8.2).
"""

from __future__ import annotations

from dataclasses import dataclass

from django.db.models import Q

from accounts.models import OfficerScope, Profile, RoleFamily
from accounts.services import get_profile
from audit.models import AuditLogEntry
from audit.writer import log
from courses.models import Course, FacultyAssignment, Section
from directory.models import Building, Department, Group

from ..constants import AudienceType, Severity


class SendDenied(Exception):
    """Raised when a send request is outside the actor's role/scope."""

    def __init__(self, reason: str, *, detail: dict | None = None):
        self.reason = reason
        self.detail = detail or {}
        super().__init__(reason)


@dataclass(frozen=True)
class SendRequest:
    audience_type: str
    severity: str
    is_urgent: bool = False
    role: str | None = None
    department: Department | None = None
    building: Building | None = None
    group: Group | None = None
    course: Course | None = None
    section: Section | None = None


def authorize_send(actor, request: SendRequest, *, audit: bool = True) -> None:
    """Return ``None`` when allowed; raise :class:`SendDenied` otherwise."""
    try:
        _authorize(actor, request)
    except SendDenied as exc:
        if audit:
            try:
                log(
                    action=AuditLogEntry.Action.SEND_DENIED,
                    actor=actor,
                    object_type="alert",
                    detail={
                        "audience_type": str(request.audience_type),
                        "severity": str(request.severity),
                        "is_urgent": bool(request.is_urgent),
                        "reason": exc.reason,
                        "target_ids": _target_ids(request),
                    },
                )
            except Exception:  # pragma: no cover - audit must not mask the denial
                # A failure to write the audit row must not turn a refusal into
                # a 500. The request is still denied; the audit outage is a
                # separate operational alarm (same rule as core/exceptions.py).
                pass
        raise


def _authorize(actor, request: SendRequest) -> None:
    if not getattr(actor, "is_authenticated", False):
        raise SendDenied("unauthenticated")

    if not getattr(actor, "is_active", False):
        # A deactivated account may still hold a token. Lookups are fail-closed:
        # an actor without a truthy is_active flag can never send.
        raise SendDenied("inactive_actor")

    if request.severity not in Severity.values:
        raise SendDenied("invalid_severity")

    if request.audience_type not in AudienceType.values:
        raise SendDenied("invalid_audience")

    profile = get_profile(actor)
    family = profile.role_family

    if family == RoleFamily.STUDENT:
        raise SendDenied("role_cannot_send")

    if not isinstance(request.is_urgent, bool):
        # A string such as "false" is truthy; never let it become urgent.
        raise SendDenied("invalid_urgency")

    _validate_audience_shape(request)

    if family == RoleFamily.FACULTY:
        _authorize_faculty(actor, request)
        return

    if family == RoleFamily.ADMIN:
        if profile.system_role == Profile.SystemRole.COMMS_ADMIN:
            return
        _authorize_officer(actor, request)
        return

    raise SendDenied("role_cannot_send")


def _authorize_faculty(actor, request: SendRequest) -> None:
    if request.severity == Severity.CRITICAL:
        raise SendDenied("faculty_severity")

    if request.audience_type not in (AudienceType.COURSE, AudienceType.SECTION):
        raise SendDenied("faculty_audience")

    if request.audience_type == AudienceType.COURSE:
        if request.course is None:
            raise SendDenied("invalid_audience")
        allowed = FacultyAssignment.objects.filter(
            user=actor,
            course=request.course,
            section__isnull=True,
        ).exists()
    else:
        if request.section is None:
            raise SendDenied("invalid_audience")
        if request.course is not None and request.course.pk != request.section.course_id:
            raise SendDenied("invalid_audience")
        allowed = FacultyAssignment.objects.filter(
            user=actor,
        ).filter(
            Q(section=request.section)
            | Q(course=request.section.course, section__isnull=True)
        ).exists()

    if not allowed:
        raise SendDenied("faculty_course_grant_required")


def _authorize_officer(actor, request: SendRequest) -> None:
    scope_type = request.audience_type

    # Campus-wide scope covers every selector.
    if OfficerScope.objects.filter(
        user=actor, scope_type=OfficerScope.ScopeType.CAMPUS_WIDE
    ).exists():
        return

    if scope_type == AudienceType.DEPARTMENT:
        if OfficerScope.objects.filter(
            user=actor,
            scope_type=OfficerScope.ScopeType.DEPARTMENT,
            department=request.department,
        ).exists():
            return

    elif scope_type == AudienceType.BUILDING:
        if OfficerScope.objects.filter(
            user=actor,
            scope_type=OfficerScope.ScopeType.BUILDING,
            building=request.building,
        ).exists():
            return

    elif scope_type == AudienceType.GROUP:
        if OfficerScope.objects.filter(
            user=actor,
            scope_type=OfficerScope.ScopeType.GROUP,
            group=request.group,
        ).exists():
            return

    elif scope_type in (AudienceType.COURSE, AudienceType.SECTION):
        course = request.course if scope_type == AudienceType.COURSE else request.section.course
        if course.department_id in _department_scope_ids(actor):
            return

    # everyone, role, and any unmatched target require CAMPUS_WIDE.
    raise SendDenied("officer_audience_out_of_scope")


def _department_scope_ids(actor) -> set[int]:
    return set(
        OfficerScope.objects.filter(
            user=actor,
            scope_type=OfficerScope.ScopeType.DEPARTMENT,
            department__isnull=False,
        ).values_list("department_id", flat=True)
    )


def _validate_audience_shape(request: SendRequest) -> None:
    """Reject missing, unsaved, or wrongly typed targets with a clean denial.

    Every role passes through here, including the comms admin, so an invalid
    selector can never be accepted just because the actor bypasses scopes.
    """
    if request.audience_type == AudienceType.ROLE:
        if request.role not in Profile.CampusRole.values:
            raise SendDenied("invalid_audience")
    elif request.audience_type == AudienceType.DEPARTMENT:
        _require_saved_model(request.department, Department)
    elif request.audience_type == AudienceType.BUILDING:
        _require_saved_model(request.building, Building)
    elif request.audience_type == AudienceType.GROUP:
        _require_saved_model(request.group, Group)
    elif request.audience_type == AudienceType.COURSE:
        _require_saved_model(request.course, Course)
    elif request.audience_type == AudienceType.SECTION:
        _require_saved_model(request.section, Section)
        if request.course is not None:
            _require_saved_model(request.course, Course)
            if request.course.pk != request.section.course_id:
                raise SendDenied("invalid_audience")


def _require_saved_model(value, model) -> None:
    if value is None or not isinstance(value, model) or value.pk is None:
        raise SendDenied("invalid_audience")


def _target_ids(request: SendRequest) -> dict:
    return {
        "role": request.role,
        "department": getattr(request.department, "pk", None),
        "building": getattr(request.building, "pk", None),
        "group": getattr(request.group, "pk", None),
        "course": getattr(request.course, "pk", None),
        "section": getattr(request.section, "pk", None),
    }
