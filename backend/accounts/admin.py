from django.contrib import admin

from .models import Profile


@admin.register(Profile)
class ProfileAdmin(admin.ModelAdmin):
    list_display = ("user", "campus_role", "system_role", "role_family", "student_id")
    list_filter = ("campus_role", "system_role")
    search_fields = ("user__username", "user__first_name", "user__last_name", "student_id")
    readonly_fields = ("role_family", "created_at", "updated_at")
    autocomplete_fields = ("user",)
