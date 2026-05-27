from allauth.account.models import EmailAddress
from allauth.account.utils import send_email_confirmation
from django.contrib.auth import get_user_model
from rest_framework import status
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView

from ..serializers import (
    EmailConfirmSerializer,
    EmailResendSerializer,
    PhoneVerifyConfirmSerializer,
    PhoneVerifyRequestSerializer,
)
from ..services import (
    AuthError,
    OTPRateLimited,
    OTPVerificationFailed,
    confirm_email_key,
    send_phone_otp,
    verify_phone_otp,
)
from ..sms import SmsSendError
from ._common import APIError, token_response

User = get_user_model()


class EmailConfirmView(APIView):
    """POST /auth/verify-email — body: {key}."""

    permission_classes = [AllowAny]
    authentication_classes: list = []

    def post(self, request):
        ser = EmailConfirmSerializer(data=request.data)
        ser.is_valid(raise_exception=True)
        try:
            user = confirm_email_key(ser.validated_data["key"])
        except AuthError as exc:
            raise APIError(str(exc))
        return Response(token_response(user, request=request))


class EmailResendView(APIView):
    """POST /auth/verify-email/resend — body: {email}."""

    permission_classes = [AllowAny]
    authentication_classes: list = []

    def post(self, request):
        ser = EmailResendSerializer(data=request.data)
        ser.is_valid(raise_exception=True)
        email = ser.validated_data["email"]
        address = EmailAddress.objects.filter(email__iexact=email).select_related("user").first()
        if address and not address.verified:
            send_email_confirmation(request, address.user, signup=False, email=email)
        # Always 200 to avoid email enumeration.
        return Response({"detail": "If the account exists, a confirmation email was sent."})


class PhoneVerifyRequestView(APIView):
    """POST /auth/verify-phone/send — body: {phone, channel?}."""

    permission_classes = [AllowAny]
    authentication_classes: list = []

    def post(self, request):
        ser = PhoneVerifyRequestSerializer(data=request.data)
        ser.is_valid(raise_exception=True)
        try:
            send_phone_otp(
                phone=ser.validated_data["phone"],
                channel=ser.validated_data.get("channel", "sms"),
            )
        except OTPRateLimited as exc:
            raise APIError(str(exc), status_code=status.HTTP_429_TOO_MANY_REQUESTS)
        except SmsSendError as exc:
            raise APIError(str(exc), status_code=status.HTTP_502_BAD_GATEWAY)
        return Response({"detail": "Code sent."}, status=status.HTTP_202_ACCEPTED)


class PhoneVerifyConfirmView(APIView):
    """POST /auth/verify-phone — body: {phone, code}.

    Marks the matching user's phone as verified and issues tokens
    if a user exists for the phone (lets clients use this as a
    passwordless re-login after OTP).
    """

    permission_classes = [AllowAny]
    authentication_classes: list = []

    def post(self, request):
        ser = PhoneVerifyConfirmSerializer(data=request.data)
        ser.is_valid(raise_exception=True)
        phone = ser.validated_data["phone"]
        try:
            verify_phone_otp(phone=phone, code=ser.validated_data["code"])
        except OTPVerificationFailed as exc:
            raise APIError(str(exc))

        user = User.objects.filter(phone=phone).first()
        if user is None:
            return Response({"detail": "Phone verified.", "registered": False})
        if not user.phone_verified:
            user.phone_verified = True
            user.save(update_fields=["phone_verified"])
        return Response({**token_response(user, request=request), "registered": True})
