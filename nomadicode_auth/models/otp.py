"""One-time codes for phone verification, login, and password reset."""

import hashlib
import hmac
import secrets
from datetime import timedelta

from django.conf import settings as django_settings
from django.db import models
from django.utils import timezone

from ..conf import settings as pkg_settings


class OTPChannel(models.TextChoices):
    SMS = "sms", "SMS"
    WHATSAPP = "whatsapp", "WhatsApp"


class OTPPurpose(models.TextChoices):
    VERIFY_PHONE = "verify_phone", "Verify phone"
    LOGIN = "login", "Login"
    PASSWORD_RESET = "password_reset", "Password reset"


def _hash(code: str) -> str:
    """HMAC the code with SECRET_KEY so DB leaks don't expose codes."""
    key = django_settings.SECRET_KEY.encode()
    return hmac.new(key, code.encode(), hashlib.sha256).hexdigest()


def _generate_code(length: int) -> str:
    upper = 10**length
    return f"{secrets.randbelow(upper):0{length}d}"


class OTPCode(models.Model):
    phone = models.CharField(max_length=48, db_index=True)
    purpose = models.CharField(max_length=32, choices=OTPPurpose.choices)
    channel = models.CharField(
        max_length=16, choices=OTPChannel.choices, default=OTPChannel.SMS
    )
    code_hash = models.CharField(max_length=128)
    attempts = models.PositiveIntegerField(default=0)
    consumed_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField()

    class Meta:
        indexes = [
            models.Index(fields=["phone", "purpose", "-created_at"]),
        ]
        ordering = ["-created_at"]

    @classmethod
    def issue(
        cls,
        *,
        phone: str,
        purpose: str,
        channel: str = OTPChannel.SMS,
    ) -> tuple["OTPCode", str]:
        """Create a new code, returning ``(otp_row, raw_code)``.

        Caller is responsible for sending ``raw_code`` over the wire.
        Any unconsumed codes for this (phone, purpose) are invalidated.
        """
        cls.objects.filter(
            phone=phone, purpose=purpose, consumed_at__isnull=True
        ).update(consumed_at=timezone.now())
        code = _generate_code(pkg_settings.OTP_LENGTH)
        row = cls.objects.create(
            phone=phone,
            purpose=purpose,
            channel=channel,
            code_hash=_hash(code),
            expires_at=timezone.now() + timedelta(seconds=pkg_settings.OTP_TTL_SECONDS),
        )
        return row, code

    @classmethod
    def verify(cls, *, phone: str, purpose: str, code: str) -> bool:
        """Return True on success, marking the row consumed.

        Returns False on bad/expired/over-attempted codes; the caller
        decides whether to translate that into 400 or 429.
        """
        row = (
            cls.objects.filter(phone=phone, purpose=purpose, consumed_at__isnull=True)
            .order_by("-created_at")
            .first()
        )
        if row is None:
            return False
        if row.expires_at < timezone.now():
            return False
        if row.attempts >= pkg_settings.OTP_MAX_ATTEMPTS:
            return False

        row.attempts += 1
        if not hmac.compare_digest(row.code_hash, _hash(code)):
            row.save(update_fields=["attempts"])
            return False

        row.consumed_at = timezone.now()
        row.save(update_fields=["attempts", "consumed_at"])
        return True

    @classmethod
    def recent_request_count(cls, *, phone: str, within_hours: int = 1) -> int:
        since = timezone.now() - timedelta(hours=within_hours)
        return cls.objects.filter(phone=phone, created_at__gte=since).count()
