from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from ..serializers import (
    PasswordChangeSerializer,
    PasswordResetConfirmSerializer,
    PasswordResetRequestSerializer,
)
from ..services import AuthError, request_password_reset, reset_password_with_key
from ._common import APIError


class PasswordResetRequestView(APIView):
    """POST /auth/password/reset — body: {email}. Always returns 200."""

    permission_classes = [AllowAny]
    authentication_classes: list = []

    def post(self, request):
        ser = PasswordResetRequestSerializer(data=request.data)
        ser.is_valid(raise_exception=True)
        request_password_reset(email=ser.validated_data["email"])
        return Response({"detail": "If the email exists, a reset link was sent."})


class PasswordResetConfirmView(APIView):
    """POST /auth/password/reset/confirm — body: {key, new_password}."""

    permission_classes = [AllowAny]
    authentication_classes: list = []

    def post(self, request):
        ser = PasswordResetConfirmSerializer(data=request.data)
        ser.is_valid(raise_exception=True)
        try:
            reset_password_with_key(
                key=ser.validated_data["key"],
                new_password=ser.validated_data["new_password"],
            )
        except AuthError as exc:
            raise APIError(str(exc))
        return Response({"detail": "Password updated."})


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
