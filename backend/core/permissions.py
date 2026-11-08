"""Coarse role gates for API views.

These only answer "may this role reach this endpoint at all". Object-level
rules (which course, which audience, which alert) live in the alerts service
layer and are always re-checked there (NFR-1, AC-3.6).
"""

from rest_framework.permissions import BasePermission

from accounts.models import Profile, RoleFamily
from accounts.services import get_profile, resolve_role_family


class IsStudent(BasePermission):
    message = "Student role required."

    def has_permission(self, request, view):
        return resolve_role_family(request.user) == RoleFamily.STUDENT


class IsFaculty(BasePermission):
    message = "Faculty role required."

    def has_permission(self, request, view):
        return resolve_role_family(request.user) == RoleFamily.FACULTY


class IsAdminRole(BasePermission):
    message = "Admin role required."

    def has_permission(self, request, view):
        return resolve_role_family(request.user) == RoleFamily.ADMIN


class IsOfficer(BasePermission):
    message = "Alert officer role required."

    def has_permission(self, request, view):
        profile = get_profile(request.user) if request.user.is_authenticated else None
        return bool(profile and profile.system_role == Profile.SystemRole.OFFICER)


class IsCommsAdmin(BasePermission):
    message = "Communications admin role required."

    def has_permission(self, request, view):
        profile = get_profile(request.user) if request.user.is_authenticated else None
        return bool(profile and profile.system_role == Profile.SystemRole.COMMS_ADMIN)
