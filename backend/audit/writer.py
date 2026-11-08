"""Single writer for the audit trail.

Services call this instead of touching the model, so every state change has
one place that enforces the "IDs and counts only" privacy rule (NFR-3).
"""

from __future__ import annotations

from typing import Any

from django.contrib.auth import get_user_model

from .models import AuditLogEntry

User = get_user_model()


def log(
    *,
    action: str,
    actor: User | None = None,
    actor_label: str = "",
    object_type: str = "",
    object_id: str | int = "",
    detail: dict[str, Any] | None = None,
) -> AuditLogEntry:
    """Append one audit entry.

    ``detail`` must contain identifiers, counts or reason codes only — never an
    email address, phone number or free-text personal data.
    """
    return AuditLogEntry.objects.create(
        actor=actor if getattr(actor, "is_authenticated", False) else None,
        actor_label=(actor_label or getattr(actor, "username", ""))[:150],
        action=action,
        object_type=object_type[:64],
        object_id=str(object_id)[:64],
        detail=detail or {},
    )
