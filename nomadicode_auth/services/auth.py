"""Signup / login / password reset orchestration.

Built on top of allauth's account internals so we don't reinvent
the email-confirmation token machinery, but exposed as plain
functions so views stay thin and the same logic can be called
from tests or admin actions.
"""

from allauth.account.models import EmailAddress, EmailConfirmationHMAC
from allauth.account.utils import send_email_confirmation
from django.contrib.auth import authenticate, get_user_model
from django.contrib.auth.tokens import default_token_generator
from django.db import IntegrityError, transaction
from django.utils.encoding import force_bytes, force_str
from django.utils.http import urlsafe_base64_decode, urlsafe_base64_encode

from ..conf import frontend_url, settings as pkg_settings
from ..models import OTPPurpose
from .otp import verify_phone_otp

User = get_user_model()


class AuthError(Exception):
    """Raised for normal auth failures (bad password, unverified, etc.)."""


class LoginRequiresVerification(AuthError):
    def __init__(self, *, email_verified: bool, phone_verified: bool):
        super().__init__("Account not verified.")
        self.email_verified = email_verified
        self.phone_verified = phone_verified


# ---------- signup ----------

@transaction.atomic
def signup_with_email(*, email: str, password: str, request=None, **extra) -> "User":
    if User.objects.filter(email__iexact=email).exists():
        raise AuthError("An account with this email already exists.")
    try:
        user = User.objects.create_user(email=email, password=password, **extra)
    except IntegrityError as exc:
        raise AuthError("An account with this email already exists.") from exc

    EmailAddress.objects.get_or_create(
        user=user, email=email, defaults={"verified": False, "primary": True}
    )
    if request is not None:
        send_email_confirmation(request, user, signup=True, email=email)
    return user


@transaction.atomic
def signup_with_phone(*, phone: str, password: str, otp_code: str, **extra) -> "User":
    """Verify the phone OTP first, then create the user with phone_verified=True."""
    verify_phone_otp(phone=phone, code=otp_code, purpose=OTPPurpose.VERIFY_PHONE)
    if User.objects.filter(phone=phone).exists():
        raise AuthError("An account with this phone already exists.")
    user = User.objects.create_user(
        phone=phone, password=password, phone_verified=True, **extra
    )
    return user


# ---------- login ----------

def login_with_credentials(*, identifier: str, password: str, request=None) -> "User":
    """Identifier may be email or phone. Enforces verification policy."""
    user = _find_user(identifier)
    if user is None:
        raise AuthError("Invalid credentials.")

    # allauth's auth backend understands email; for phone we fall back to manual check.
    authed = None
    if user.email and identifier.lower() == (user.email or "").lower():
        authed = authenticate(request=request, username=user.email, password=password)
    if authed is None and user.check_password(password):
        authed = user
    if authed is None:
        raise AuthError("Invalid credentials.")

    _enforce_verification(authed, identifier)
    return authed


def _find_user(identifier: str):
    if "@" in identifier:
        return User.objects.filter(email__iexact=identifier).first()
    return User.objects.filter(phone=identifier).first()


def _enforce_verification(user, identifier: str) -> None:
    email_required = pkg_settings.REQUIRE_VERIFIED_EMAIL
    phone_required = pkg_settings.REQUIRE_VERIFIED_PHONE

    used_email = "@" in identifier
    if used_email and email_required and not user.email_verified:
        raise LoginRequiresVerification(
            email_verified=False, phone_verified=user.phone_verified
        )
    if not used_email and phone_required and not user.phone_verified:
        raise LoginRequiresVerification(
            email_verified=user.email_verified, phone_verified=False
        )


# ---------- email verification ----------

def confirm_email_key(key: str) -> "User":
    confirmation = EmailConfirmationHMAC.from_key(key)
    if confirmation is None:
        raise AuthError("Invalid or expired confirmation link.")
    confirmation.confirm(request=None)
    email = confirmation.email_address
    user = email.user
    if hasattr(user, "email_verified") and not user.email_verified:
        user.email_verified = True
        user.save(update_fields=["email_verified"])
    return user


# ---------- password reset ----------

def request_password_reset(*, email: str) -> str | None:
    """Return the reset URL (also emailed). Returns None silently if no such user."""
    user = User.objects.filter(email__iexact=email).first()
    if user is None:
        return None

    uid = urlsafe_base64_encode(force_bytes(user.pk))
    token = default_token_generator.make_token(user)
    key = f"{uid}-{token}"
    url = frontend_url(pkg_settings.FRONTEND_PASSWORD_RESET_PATH, key=key)

    # Hand off to allauth's mailer for the actual email body.
    from allauth.account.adapter import get_adapter

    get_adapter().send_mail(
        "account/email/password_reset_key", email, {"password_reset_url": url, "user": user}
    )
    return url


def reset_password_with_key(*, key: str, new_password: str) -> "User":
    try:
        uidb64, token = key.split("-", 1)
    except ValueError as exc:
        raise AuthError("Invalid reset link.") from exc

    try:
        uid = force_str(urlsafe_base64_decode(uidb64))
        user = User.objects.get(pk=uid)
    except (User.DoesNotExist, ValueError, TypeError) as exc:
        raise AuthError("Invalid reset link.") from exc

    if not default_token_generator.check_token(user, token):
        raise AuthError("Invalid or expired reset link.")

    user.set_password(new_password)
    user.save(update_fields=["password"])
    return user
