"""URL patterns for nomadicode-auth.

Mount under any prefix you like::

    path("auth/", include("nomadicode_auth.urls")),

Exposes:
    POST /signup
    POST /login
    POST /logout
    POST /refresh
    GET  /me
    PATCH /me
    POST /verify-email
    POST /verify-email/resend
    POST /verify-phone
    POST /verify-phone/send
    POST /password/reset
    POST /password/reset/confirm
    POST /password/change
    POST /social/<provider>/         (provider in NOMADICODE_AUTH["SOCIAL_PROVIDERS"])
"""

from django.urls import path

from .conf import settings as pkg_settings
from .views import (
    EmailConfirmView,
    EmailResendView,
    LoginView,
    LogoutView,
    MeView,
    PasswordChangeView,
    PasswordResetConfirmView,
    PasswordResetRequestView,
    PhoneVerifyConfirmView,
    PhoneVerifyRequestView,
    RefreshTokenView,
    SignupView,
    SocialLoginView,
)

app_name = "nomadicode_auth"

urlpatterns = [
    path("signup", SignupView.as_view(), name="signup"),
    path("login", LoginView.as_view(), name="login"),
    path("logout", LogoutView.as_view(), name="logout"),
    path("refresh", RefreshTokenView.as_view(), name="refresh"),
    path("me", MeView.as_view(), name="me"),
    path("verify-email", EmailConfirmView.as_view(), name="verify-email"),
    path("verify-email/resend", EmailResendView.as_view(), name="verify-email-resend"),
    path("verify-phone", PhoneVerifyConfirmView.as_view(), name="verify-phone"),
    path("verify-phone/send", PhoneVerifyRequestView.as_view(), name="verify-phone-send"),
    path("password/reset", PasswordResetRequestView.as_view(), name="password-reset"),
    path(
        "password/reset/confirm",
        PasswordResetConfirmView.as_view(),
        name="password-reset-confirm",
    ),
    path("password/change", PasswordChangeView.as_view(), name="password-change"),
]

# Only mount /social/<provider>/ for enabled providers — anything else 404s.
for _provider in pkg_settings.SOCIAL_PROVIDERS:
    urlpatterns.append(
        path(
            f"social/{_provider}",
            SocialLoginView.as_view(),
            {"provider": _provider},
            name=f"social-{_provider}",
        )
    )
