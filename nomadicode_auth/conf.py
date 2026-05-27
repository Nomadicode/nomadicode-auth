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
    # Social providers we wire up by default. Projects can add/remove
    # by setting NOMADICODE_AUTH["SOCIAL_PROVIDERS"]; the package only
    # exposes /auth/social/<provider>/ for entries listed here.
    "SOCIAL_PROVIDERS": ("google", "facebook"),
    # Email "from" used by the package's mailer adapter.
    "EMAIL_SUBJECT_PREFIX": "",
    # SMS backend (dotted module path). Convention mirrors Django's
    # EMAIL_BACKEND. The top-level ``SMS_BACKEND`` setting takes
    # precedence so projects can write ``SMS_BACKEND = "..."``
    # directly without nesting it under NOMADICODE_AUTH.
    "SMS_BACKEND": "nomadicode_auth.sms.twilio.TwilioBackend",
}


class _Settings:
    """Tiny accessor — `from nomadicode_auth.conf import settings`."""

    def __getattr__(self, name):
        if name == "SMS_BACKEND":
            return getattr(
                django_settings,
                "SMS_BACKEND",
                self._user_overrides().get("SMS_BACKEND", DEFAULTS["SMS_BACKEND"]),
            )
        if name in DEFAULTS:
            return self._user_overrides().get(name, DEFAULTS[name])
        raise AttributeError(name)

    @staticmethod
    def _user_overrides():
        return getattr(django_settings, "NOMADICODE_AUTH", {}) or {}


settings = _Settings()


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
