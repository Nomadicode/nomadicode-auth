from rest_framework import status
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from ..serializers import (
    PasswordChangeSerializer,
    PasswordResetConfirmSerializer,
    PasswordResetRequestSerializer,
)
from ..services import (
    AuthError,
    OTPRateLimited,
    OTPVerificationFailed,
    request_password_reset,
    request_password_reset_otp,
    reset_password_with_key,
    reset_password_with_otp,
)
from ..sms import SmsSendError
from ._common import APIError, token_response


class PasswordResetRequestView(APIView):
    """POST /auth/password/reset — body: {email} or {phone, channel?}.

    Always returns 200/202 without revealing whether the account exists.
    """

    permission_classes = [AllowAny]
    authentication_classes: list = []

    def post(self, request):
        ser = PasswordResetRequestSerializer(data=request.data)
        ser.is_valid(raise_exception=True)

        if ser.validated_data.get("email"):
            request_password_reset(email=ser.validated_data["email"])
            return Response({"detail": "If the email exists, a reset link was sent."})

        try:
            request_password_reset_otp(
                phone=ser.validated_data["phone"],
                channel=ser.validated_data.get("channel", "sms"),
            )
        except OTPRateLimited as exc:
            raise APIError(str(exc), status_code=status.HTTP_429_TOO_MANY_REQUESTS)
        except SmsSendError as exc:
            raise APIError(str(exc), status_code=status.HTTP_502_BAD_GATEWAY)
        return Response(
            {"detail": "If the phone exists, a code was sent."},
            status=status.HTTP_202_ACCEPTED,
        )


class PasswordResetConfirmView(APIView):
    """POST /auth/password/reset/confirm — body: {key, new_password} or
    {phone, code, new_password}.

    Returns a full token payload (access/refresh/user) so clients can adopt
    the session immediately after a successful reset.
    """

    permission_classes = [AllowAny]
    authentication_classes: list = []

    def post(self, request):
        ser = PasswordResetConfirmSerializer(data=request.data)
        ser.is_valid(raise_exception=True)
        new_password = ser.validated_data["new_password"]

        try:
            if ser.validated_data.get("key"):
                user = reset_password_with_key(
                    key=ser.validated_data["key"],
                    new_password=new_password,
                )
            else:
                user = reset_password_with_otp(
                    phone=ser.validated_data["phone"],
                    code=ser.validated_data["code"],
                    new_password=new_password,
                )
        except OTPVerificationFailed as exc:
            raise APIError(str(exc))
        except AuthError as exc:
            raise APIError(str(exc))
        return Response(token_response(user, request=request))


class PasswordChangeView(APIView):
    """POST /auth/password/change — body: {old_password, new_password}."""

    permission_classes = [IsAuthenticated]

    def post(self, request):
        ser = PasswordChangeSerializer(data=request.data)
        ser.is_valid(raise_exception=True)
        user = request.user
        if not user.check_password(ser.validated_data["old_password"]):
            raise APIError("Current password is incorrect.")
        user.set_password(ser.validated_data["new_password"])
        user.save(update_fields=["password"])
        return Response({"detail": "Password updated."})
