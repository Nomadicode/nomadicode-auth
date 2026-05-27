from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as DjangoUserAdmin

from .models import User


@admin.register(User)
class UserAdmin(DjangoUserAdmin):
    list_display = ("email", "phone", "first_name", "last_name", "email_verified", "phone_verified", "is_staff")
    list_filter = ("is_staff", "is_superuser", "is_active", "email_verified", "phone_verified")
    search_fields = ("email", "phone", "first_name", "last_name")
    ordering = ("-date_joined",)
    fieldsets = (
        (None, {"fields": ("email", "phone", "password")}),
        ("Profile", {"fields": ("first_name", "last_name")}),
        ("Verification", {"fields": ("email_verified", "phone_verified")}),
        ("Permissions", {"fields": ("is_active", "is_staff", "is_superuser", "groups", "user_permissions")}),
        ("Important dates", {"fields": ("last_login", "date_joined")}),
    )
    add_fieldsets = (
        (None, {
            "classes": ("wide",),
            "fields": ("email", "phone", "password1", "password2"),
        }),
    )
