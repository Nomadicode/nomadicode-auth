from rest_framework import serializers

from ..models import OTPChannel


class EmailConfirmSerializer(serializers.Serializer):
    key = serializers.CharField()


class EmailResendSerializer(serializers.Serializer):
    email = serializers.EmailField()


class PhoneVerifyRequestSerializer(serializers.Serializer):
    phone = serializers.CharField(max_length=48)
    channel = serializers.ChoiceField(
        choices=OTPChannel.choices, default=OTPChannel.SMS, required=False
    )


class PhoneVerifyConfirmSerializer(serializers.Serializer):
    phone = serializers.CharField(max_length=48)
    code = serializers.CharField(max_length=12)
