"""Single place to read nomadicode-auth settings with sane defaults.

Projects override anything by setting ``NOMADICODE_AUTH = {...}`` in
their Django settings, or by setting the named top-level setting
(e.g. ``SMS_BACKEND``) — top-level wins for the few keys that have
a conventional Django-wide name.
"""

from django.conf import settings as django_settings

DEFAULTS = {
    # Frontend URLs used in email templates + social redirect targets.
    # The package will substitute these into the standard allauth
    # HEADLESS_FRONTEND_URLS shape, so projects only set them once.
    "FRONTEND_URL": "http://localhost:8080",
    "FRONTEND_EMAIL_CONFIRM_PATH": "/auth/confirm-email/{key}",
    "FRONTEND_PASSWORD_RESET_PATH": "/auth/reset-password/{key}",
    "FRONTEND_LOGIN_ERROR_PATH": "/auth/login-error",
    # Login policy.
    "LOGIN_METHODS": ("email", "phone"),  # any subset of email/phone/username
    "REQUIRE_VERIFIED_EMAIL": True,
    "REQUIRE_VERIFIED_PHONE": True,
    # When True, phone signup requires a verified OTP code (the account is
    # created with phone_verified=True). Set False to allow password-only phone
    # signup with no verification — the account is created unverified and can be
    # verified later via /verify-phone/send.
    "REQUIRE_PHONE_SIGNUP_OTP": True,
    # JWT lifetimes (seconds).
    "JWT_ACCESS_TTL": 60 * 60,
    "JWT_REFRESH_TTL": 60 * 60 * 24 * 7,
    "JWT_ROTATE_REFRESH": True,
    "JWT_ALGORITHM": "HS256",
    # OTP policy.
    "OTP_LENGTH": 6,
    "OTP_TTL_SECONDS": 5 * 60,
    "OTP_MAX_ATTEMPTS": 5,
    "OTP_RATE_LIMIT_PER_HOUR": 5,
    # Social login config: provider -> credentials, e.g.
    #   "SOCIAL": {"google": {"client_id": "...", "secret": "..."}}
    # The listed providers get a /auth/social/<provider>/ endpoint and
    # their credentials are injected into SOCIALACCOUNT_PROVIDERS.
    # ``SOCIAL_PROVIDERS`` (a plain tuple of names) still works for
    # projects that keep credentials in SocialApp rows instead.
    "SOCIAL": {},
    "SOCIAL_PROVIDERS": ("google", "facebook"),
    # Email "from" used by the package's mailer adapter.
    "EMAIL_SUBJECT_PREFIX": "",
    # SMS config lives in one dict: ``BACKEND`` (dotted path) plus any
    # backend-specific options, e.g.
    #   "SMS": {
    #       "BACKEND": "nomadicode_auth.sms.twilio.TwilioBackend",
    #       "TWILIO_ACCOUNT_SID": "...",
    #       "TWILIO_AUTH_TOKEN": "...",
    #       "TWILIO_PHONE_FROM": "+1...",
    #   }
    # Legacy spellings keep working: a top-level ``SMS_BACKEND`` /
    # ``TWILIO_*`` setting or NOMADICODE_AUTH["SMS_BACKEND"].
    "SMS": {},
    "SMS_BACKEND": "nomadicode_auth.sms.twilio.TwilioBackend",
}


class _Settings:
    """Tiny accessor — `from nomadicode_auth.conf import settings`."""

    def __getattr__(self, name):
        overrides = self._user_overrides()
        if name == "SMS_BACKEND":
            return (
                (overrides.get("SMS") or {}).get("BACKEND")
                or getattr(django_settings, "SMS_BACKEND", None)
                or overrides.get("SMS_BACKEND", DEFAULTS["SMS_BACKEND"])
            )
        if name == "SOCIAL_PROVIDERS":
            if "SOCIAL_PROVIDERS" in overrides:
                return overrides["SOCIAL_PROVIDERS"]
            if overrides.get("SOCIAL"):
                return tuple(overrides["SOCIAL"])
            return DEFAULTS["SOCIAL_PROVIDERS"]
        if name in DEFAULTS:
            return overrides.get(name, DEFAULTS[name])
        raise AttributeError(name)

    @staticmethod
    def _user_overrides():
        return getattr(django_settings, "NOMADICODE_AUTH", {}) or {}


settings = _Settings()


def sms_option(name: str, default: str = "") -> str:
    """Backend option lookup: NOMADICODE_AUTH["SMS"][name] first, then the
    legacy top-level Django setting of the same name (e.g. TWILIO_AUTH_TOKEN)."""
    sms = settings.SMS or {}
    if name in sms:
        return sms[name]
    return getattr(django_settings, name, default)


def frontend_url(path_template: str = "", **kwargs) -> str:
    """Join FRONTEND_URL with a template path, leaving allauth-style
    placeholders intact when kwargs aren't passed."""
    base = settings.FRONTEND_URL.rstrip("/")
    suffix = path_template.format(**kwargs) if kwargs else path_template
    if not suffix:
        return base
    if not suffix.startswith("/"):
        suffix = "/" + suffix
    return base + suffix
