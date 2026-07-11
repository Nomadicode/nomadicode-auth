from allauth.headless.tokens.strategies.jwt.internal import (
    create_access_token,
    validate_refresh_token,
)

try:
    from allauth.headless.tokens.strategies.jwt.internal import (
        invalidate_refresh_token,
    )
except ImportError:  # pragma: no cover - older allauth rotates internally
    invalidate_refresh_token = None

# `rotate_refresh_token` was renamed to `create_refresh_token` in
# django-allauth ~65.x. Support both so we don't have to pin a specific
# release of the upstream package.
try:
    from allauth.headless.tokens.strategies.jwt.internal import (
        rotate_refresh_token,
    )
except ImportError:  # pragma: no cover - newer allauth
    from allauth.headless.tokens.strategies.jwt.internal import (
        create_refresh_token as rotate_refresh_token,
    )
from django.contrib.auth import logout as django_logout
from rest_framework import status
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from ..conf import settings as pkg_settings
from ..serializers import (
    EmailSignupSerializer,
    LoginSerializer,
    PhoneSignupSerializer,
    UserMeSerializer,
)
from ..services import (
    AuthError,
    LoginRequiresVerification,
    login_with_credentials,
    signup_with_email,
    signup_with_phone,
)
from ._common import APIError, token_response


def _strategy_claims(user) -> dict:
    """Claims from the configured HEADLESS_TOKEN_STRATEGY, so tokens minted
    on refresh carry the same custom claims (e.g. ``user_id``) as the ones
    minted at login. ``claims`` became a required positional argument of
    ``create_access_token`` in django-allauth ~65.x."""
    from allauth.headless import app_settings as headless_settings

    strategy = headless_settings.TOKEN_STRATEGY
    get_claims = getattr(strategy, "get_claims", None)
    return get_claims(user) if get_claims else {}


class SignupView(APIView):
    """POST /auth/signup

    Body must include either email+password (email flow) or
    phone+password+otp_code (phone flow). Use /auth/verify-phone/send
    to obtain the OTP first.
    """

    permission_classes = [AllowAny]
    authentication_classes: list = []

    def post(self, request):
        if "phone" in request.data:
            return self._phone_signup(request)
        return self._email_signup(request)

    def _email_signup(self, request):
        ser = EmailSignupSerializer(data=request.data)
        ser.is_valid(raise_exception=True)
        try:
            user = signup_with_email(**ser.validated_data, request=request)
        except AuthError as exc:
            raise APIError(str(exc))
        # Email needs verification before we hand out tokens.
        if pkg_settings.REQUIRE_VERIFIED_EMAIL:
            return Response(
                {
                    "detail": "Account created. Check your email to verify.",
                    "user": UserMeSerializer(user, context={"request": request}).data,
                },
                status=status.HTTP_201_CREATED,
            )
        return Response(
            token_response(user, request=request), status=status.HTTP_201_CREATED
        )

    def _phone_signup(self, request):
        ser = PhoneSignupSerializer(data=request.data)
        ser.is_valid(raise_exception=True)
        try:
            user = signup_with_phone(**ser.validated_data)
        except AuthError as exc:
            raise APIError(str(exc))
        return Response(
            token_response(user, request=request), status=status.HTTP_201_CREATED
        )


class LoginView(APIView):
    """POST /auth/login — body: {identifier, password}."""

    permission_classes = [AllowAny]
    authentication_classes: list = []

    def post(self, request):
        ser = LoginSerializer(data=request.data)
        ser.is_valid(raise_exception=True)
        try:
            user = login_with_credentials(
                identifier=ser.validated_data["identifier"],
                password=ser.validated_data["password"],
                request=request,
            )
        except LoginRequiresVerification as exc:
            raise APIError(
                str(exc),
                code="verification_required",
                status_code=status.HTTP_403_FORBIDDEN,
            )
        except AuthError as exc:
            raise APIError(
                str(exc),
                code="invalid_credentials",
                status_code=status.HTTP_401_UNAUTHORIZED,
            )
        return Response(token_response(user, request=request))


class LogoutView(APIView):
    """POST /auth/logout — best-effort session teardown."""

    permission_classes = [AllowAny]

    def post(self, request):
        django_logout(request)
        return Response({"detail": "Logged out."})


class RefreshTokenView(APIView):
    """POST /auth/refresh — body: {refresh}."""

    permission_classes = [AllowAny]
    authentication_classes: list = []

    def post(self, request):
        refresh = request.data.get("refresh")
        if not refresh:
            raise APIError("`refresh` token is required.")

        result = validate_refresh_token(refresh)
        if result is None:
            raise APIError(
                "Invalid or expired refresh token.",
                status_code=status.HTTP_401_UNAUTHORIZED,
                code="invalid_refresh",
            )
        user, session, payload = result
        access = create_access_token(user, session, _strategy_claims(user))
        if pkg_settings.JWT_ROTATE_REFRESH:
            if invalidate_refresh_token is not None:
                invalidate_refresh_token(session, payload)
            new_refresh = rotate_refresh_token(user, session)
        else:
            new_refresh = refresh
        # create/invalidate mutate nested session state without flagging the
        # session as modified — persist explicitly or the rotated token's
        # server-side state is lost and the next refresh 401s.
        session.save()
        return Response({"access": access, "refresh": new_refresh})


class MeView(APIView):
    """GET /auth/me — current user; PATCH /auth/me — update profile."""

    permission_classes = [IsAuthenticated]

    def get(self, request):
        return Response(
            UserMeSerializer(request.user, context={"request": request}).data
        )

    def patch(self, request):
        ser = UserMeSerializer(
            request.user, data=request.data, partial=True, context={"request": request}
        )
        ser.is_valid(raise_exception=True)
        ser.save()
        return Response(ser.data)
