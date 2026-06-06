from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin

from apps.accounts.models import User


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    ordering = ("email",)
    list_display = ("email", "username", "full_name", "role", "is_staff", "is_active")
    list_filter = ("role", "is_staff", "is_superuser", "is_active", "is_deleted")
    search_fields = ("email", "username", "full_name")
    fieldsets = (
        (None, {"fields": ("email", "password")}),
        ("Personal info", {"fields": ("username", "full_name", "role")}),
        ("Permissions", {"fields": ("is_active", "is_staff", "is_superuser", "groups", "user_permissions")}),
        ("Important dates", {"fields": ("last_login_at", "created_at", "updated_at")}),
        ("Soft delete", {"fields": ("is_deleted",)}),
    )
    add_fieldsets = (
        (
            None,
            {
                "classes": ("wide",),
                "fields": ("email", "username", "full_name", "role", "password1", "password2", "is_staff", "is_superuser"),
            },
        ),
    )
    readonly_fields = ("created_at", "updated_at", "last_login_at")

