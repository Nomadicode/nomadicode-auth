from django.contrib.auth import get_user_model
from django.contrib.auth.password_validation import validate_password
from rest_framework import serializers

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
    email = serializers.EmailField()


class PasswordResetConfirmSerializer(serializers.Serializer):
    key = serializers.CharField()
    new_password = serializers.CharField(write_only=True, min_length=8)

    def validate_new_password(self, value):
        validate_password(value)
        return value


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
