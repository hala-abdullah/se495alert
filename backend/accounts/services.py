"""Authentication and role-resolution services.

Views call these functions; they never derive roles themselves. Keeping the
derivation here means the Flutter client and any future client receive the
same answer for the same account (NFR-1).
"""

from __future__ import annotations

from django.contrib.auth import authenticate, get_user_model

from .models import Profile, RoleFamily

User = get_user_model()


def get_profile(user: User) -> Profile:
    """Return the profile, creating a safe default for unseeded accounts.

    A missing profile must never grant elevated rights. The default is a
    student recipient.
    """
    profile, _ = Profile.objects.get_or_create(user=user)
    return profile


def resolve_role_family(user: User) -> str:
    if not getattr(user, "is_authenticated", False):
        return ""
    return get_profile(user).role_family


def authenticate_credentials(*, username: str, password: str):
    """Return the user for valid credentials, else ``None``.

    ``ModelBackend`` also rejects inactive users, which is what we want.
    """
    if not username or not password:
        return None
    return authenticate(username=username, password=password)


def build_identity(user: User) -> dict:
    """The payload the Flutter app uses to configure its navigation.

    It is a *presentation* hint only. Every endpoint re-checks permissions
    server-side (AC-3.6).
    """
    profile = get_profile(user)
    family = profile.role_family
    is_admin = family == RoleFamily.ADMIN
    is_comms_admin = profile.system_role == Profile.SystemRole.COMMS_ADMIN

    if is_admin:
        audiences = ["everyone", "role", "department", "building", "group", "course", "section"]
    elif family == RoleFamily.FACULTY:
        audiences = ["course", "section"]
    else:
        audiences = []

    return {
        "id": user.pk,
        "username": user.username,
        "display_name": profile.display_name,
        "student_id": profile.student_id,
        "role_family": family,
        "campus_role": profile.campus_role,
        "system_role": profile.system_role,
        "permissions": {
            "can_send": family in (RoleFamily.FACULTY, RoleFamily.ADMIN),
            "can_send_critical": is_admin,
            "can_manage_senders": is_comms_admin,
            "can_manage_categories": is_comms_admin,
            "can_moderate_comments": is_comms_admin,
            "can_view_system_reports": is_comms_admin,
            "audience_types": audiences,
        },
    }
