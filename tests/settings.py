"""Minimal settings exercising the NOMADICODE_AUTH-only configuration."""

SECRET_KEY = "test-secret-key"
DEBUG = True
USE_TZ = True

DATABASES = {"default": {"ENGINE": "django.db.backends.sqlite3", "NAME": ":memory:"}}

INSTALLED_APPS = [
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.sites",
    "allauth",
    "allauth.account",
    "allauth.socialaccount",
    "allauth.socialaccount.providers.google",
    "allauth.headless",
    "rest_framework",
    "nomadicode_auth",
    "nomadicode_auth.users",
]

SITE_ID = 1
AUTH_USER_MODEL = "nomadicode_auth_users.User"

MIDDLEWARE = [
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "allauth.account.middleware.AccountMiddleware",
]

AUTHENTICATION_BACKENDS = (
    "django.contrib.auth.backends.ModelBackend",
    "allauth.account.auth_backends.AuthenticationBackend",
)

ROOT_URLCONF = "tests.urls"

# Project-defined allauth setting — must survive defaults injection.
HEADLESS_JWT_ALGORITHM = "HS512"

NOMADICODE_AUTH = {
    "JWT_ACCESS_TTL": 123,
    "JWT_REFRESH_TTL": 456,
    "SMS": {
        "BACKEND": "nomadicode_auth.sms.dummy.DummyBackend",
        "TWILIO_ACCOUNT_SID": "sid-from-sms-dict",
    },
    "SOCIAL": {
        "google": {"client_id": "google-cid", "secret": "google-secret"},
    },
}
