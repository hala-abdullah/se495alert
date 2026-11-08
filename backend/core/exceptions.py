"""API error handling.

Two jobs:
1. Normalize DRF errors into ``{"detail": ..., "fields": {...}}``.
2. Record every 401/403 as a ``REQUEST_DENIED`` audit entry (AC-3.8).

Audit failure must never turn a rejection into a 500, so logging is guarded.
"""

from __future__ import annotations

from rest_framework.views import exception_handler


def custom_exception_handler(exc, context):
    response = exception_handler(exc, context)
    if response is None:
        return response

    _normalize(response)

    if response.status_code in (401, 403):
        _audit_denial(response, context)

    return response


def _normalize(response) -> None:
    data = response.data
    if isinstance(data, dict):
        if "detail" not in data and data:
            response.data = {"detail": "Validation failed.", "fields": data}
        elif "detail" in data and not isinstance(data["detail"], str):
            response.data = {"detail": str(data["detail"])}
    elif isinstance(data, list):
        response.data = {"detail": " ".join(str(item) for item in data)}


def _audit_denial(response, context) -> None:
    try:
        from audit.models import AuditLogEntry
        from audit.writer import log

        request = context.get("request")
        if request is None:
            return

        user = getattr(request, "user", None)
        actor = user if getattr(user, "is_authenticated", False) else None
        reason = response.data.get("detail", "") if isinstance(response.data, dict) else ""
        path = getattr(request, "path", "")[:64]

        log(
            action=AuditLogEntry.Action.REQUEST_DENIED,
            actor=actor,
            object_type="endpoint",
            object_id=path,
            detail={
                "method": getattr(request, "method", "")[:8],
                "status": response.status_code,
                "reason": str(reason)[:160],
            },
        )
    except Exception:  # pragma: no cover - audit must not break the response
        pass
