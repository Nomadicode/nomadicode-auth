from django.contrib import admin

from .models import OTPCode


@admin.register(OTPCode)
class OTPCodeAdmin(admin.ModelAdmin):
    list_display = (
        "phone",
        "purpose",
        "channel",
        "attempts",
        "created_at",
        "expires_at",
        "consumed_at",
    )
    list_filter = ("purpose", "channel")
    search_fields = ("phone",)
    readonly_fields = ("code_hash", "created_at")
