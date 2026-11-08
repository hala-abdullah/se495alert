from django.contrib import admin

from .models import AuditLogEntry


@admin.register(AuditLogEntry)
class AuditLogEntryAdmin(admin.ModelAdmin):
    """Read-only developer view. The audit trail has no mutation path."""

    list_display = ("created_at", "action", "actor", "actor_label", "object_type", "object_id")
    list_filter = ("action", "object_type")
    search_fields = ("actor__username", "actor_label", "object_id")
    readonly_fields = tuple(field.name for field in AuditLogEntry._meta.fields)
    date_hierarchy = "created_at"

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False
