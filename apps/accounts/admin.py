"""Admin site configuration for user accounts."""

from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin

from apps.accounts.models import User


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    """Custom admin configuration presenting role and approval fields."""

    list_display: tuple[str, ...] = (
        "username",
        "email",
        "role",
        "is_approved",
        "is_staff",
    )
    list_filter: tuple[str, ...] = (
        "role",
        "is_approved",
        "is_staff",
        "is_superuser",
    )
    search_fields: tuple[str, ...] = ("username", "email")
    fieldsets: tuple = BaseUserAdmin.fieldsets + (
        ("Portal Attributes", {"fields": ("role", "is_approved")}),
    )
    add_fieldsets: tuple = BaseUserAdmin.add_fieldsets + (
        ("Portal Attributes", {"fields": ("email", "role", "is_approved")}),
    )
