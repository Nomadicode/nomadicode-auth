from django.contrib.auth import get_user_model
from django.contrib.auth.password_validation import validate_password
from rest_framework import serializers

from ..models import OTPChannel

User = get_user_model()


class EmailSignupSerializer(serializers.Serializer):
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True, min_length=8)
    first_name = serializers.CharField(required=False, allow_blank=True, max_length=128)
    last_name = serializers.CharField(required=False, allow_blank=True, max_length=128)

    def validate_password(self, value):
        validate_password(value)
        return value


class PhoneSignupSerializer(serializers.Serializer):
    phone = serializers.CharField(max_length=48)
    password = serializers.CharField(write_only=True, min_length=8)
    otp_code = serializers.CharField(max_length=12)
    first_name = serializers.CharField(required=False, allow_blank=True, max_length=128)
    last_name = serializers.CharField(required=False, allow_blank=True, max_length=128)

    def validate_password(self, value):
        validate_password(value)
        return value


class LoginSerializer(serializers.Serializer):
    """``identifier`` is either an email or a phone."""

    identifier = serializers.CharField()
    password = serializers.CharField(write_only=True)


class PasswordResetRequestSerializer(serializers.Serializer):
    """Provide ``email`` (reset link) or ``phone`` (OTP code), not both."""

    email = serializers.EmailField(required=False)
    phone = serializers.CharField(max_length=48, required=False)
    channel = serializers.ChoiceField(
        choices=OTPChannel.choices, default=OTPChannel.SMS, required=False
    )

    def validate(self, attrs):
        if bool(attrs.get("email")) == bool(attrs.get("phone")):
            raise serializers.ValidationError("Provide exactly one of 'email' or 'phone'.")
        return attrs


class PasswordResetConfirmSerializer(serializers.Serializer):
    """Provide ``key`` (email link) or ``phone`` + ``code`` (OTP), not both."""

    key = serializers.CharField(required=False)
    phone = serializers.CharField(max_length=48, required=False)
    code = serializers.CharField(max_length=12, required=False)
    new_password = serializers.CharField(write_only=True, min_length=8)

    def validate_new_password(self, value):
        validate_password(value)
        return value

    def validate(self, attrs):
        has_key = bool(attrs.get("key"))
        has_otp = bool(attrs.get("phone")) and bool(attrs.get("code"))
        if has_key == has_otp:
            raise serializers.ValidationError(
                "Provide either 'key' or both 'phone' and 'code'."
            )
        return attrs


class PasswordChangeSerializer(serializers.Serializer):
    old_password = serializers.CharField(write_only=True)
    new_password = serializers.CharField(write_only=True, min_length=8)

    def validate_new_password(self, value):
        validate_password(value)
        return value


class UserMeSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = (
            "id",
            "email",
            "phone",
            "first_name",
            "last_name",
            "email_verified",
            "phone_verified",
            "is_staff",
            "date_joined",
        )
        read_only_fields = (
            "id",
            "email_verified",
            "phone_verified",
            "is_staff",
            "date_joined",
        )
