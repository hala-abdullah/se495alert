"""Append-only audit trail (US-7, NFR-5, AC-3.8).

Rows are written by service functions and by the API exception handler.
There is deliberately no update or delete path exposed.
"""

from django.conf import settings
from django.db import models


class AuditLogEntry(models.Model):
    class Action(models.TextChoices):
        LOGIN_SUCCEEDED = "LOGIN_SUCCEEDED", "Login succeeded"
        LOGIN_FAILED = "LOGIN_FAILED", "Login failed"
        LOGOUT = "LOGOUT", "Logout"
        REQUEST_DENIED = "REQUEST_DENIED", "Request denied"
        SEND_OK = "SEND_OK", "Alert sent"
        SEND_DENIED = "SEND_DENIED", "Alert send denied"
        ACK = "ACK", "Alert acknowledged"
        READ = "READ", "Alert read"
        SCOPE_GRANTED = "SCOPE_GRANTED", "Officer scope granted"
        SCOPE_REVOKED = "SCOPE_REVOKED", "Officer scope revoked"
        COURSE_GRANT_GRANTED = "COURSE_GRANT_GRANTED", "Course grant granted"
        COURSE_GRANT_REVOKED = "COURSE_GRANT_REVOKED", "Course grant revoked"
        PREF_UPDATE = "PREF_UPDATE", "Preferences updated"
        COMMENT_POST = "COMMENT_POST", "Comment posted"
        COMMENT_REMOVE = "COMMENT_REMOVE", "Comment removed"
        CATEGORY_CHANGE = "CATEGORY_CHANGE", "Category changed"
        REMINDER_DISPATCH = "REMINDER_DISPATCH", "Reminder dispatched"

    actor = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="audit_entries",
        help_text="Null for anonymous requests and system actions.",
    )
    actor_label = models.CharField(
        max_length=150,
        blank=True,
        help_text="Attempted username or system label; never a contact address.",
    )
    action = models.CharField(max_length=32, choices=Action.choices)
    object_type = models.CharField(max_length=64, blank=True)
    object_id = models.CharField(max_length=64, blank=True)
    detail = models.JSONField(
        default=dict,
        blank=True,
        help_text="IDs, counts and reasons only. No contact data (NFR-3).",
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at", "-id"]
        indexes = [
            models.Index(fields=["action", "created_at"]),
            models.Index(fields=["actor", "created_at"]),
        ]

    def save(self, *args, **kwargs):
        if self.pk is not None:
            raise ValueError("Audit log entries are append-only")
        return super().save(*args, **kwargs)

    def __str__(self) -> str:
        return f"{self.created_at:%Y-%m-%d %H:%M:%S} {self.action}"
