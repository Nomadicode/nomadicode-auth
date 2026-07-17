"""Phone signup with and without OTP verification (REQUIRE_PHONE_SIGNUP_OTP)."""

import pytest
from django.test import override_settings

from nomadicode_auth.serializers import PhoneSignupSerializer
from nomadicode_auth.services.auth import signup_with_phone

NO_OTP = {"REQUIRE_PHONE_SIGNUP_OTP": False}
REQUIRE_OTP = {"REQUIRE_PHONE_SIGNUP_OTP": True}


class TestSerializerOtpRequirement:
    @override_settings(NOMADICODE_AUTH=REQUIRE_OTP)
    def test_otp_required_by_default(self):
        ser = PhoneSignupSerializer(
            data={"phone": "+14155551234", "password": "s3cretpass"}
        )
        assert not ser.is_valid()
        assert "otp_code" in ser.errors

    @override_settings(NOMADICODE_AUTH=NO_OTP)
    def test_otp_optional_when_disabled(self):
        ser = PhoneSignupSerializer(
            data={"phone": "+14155551234", "password": "s3cretpass"}
        )
        assert ser.is_valid(), ser.errors


@pytest.mark.django_db
@override_settings(NOMADICODE_AUTH=NO_OTP)
def test_signup_without_otp_creates_unverified_user():
    user = signup_with_phone(phone="+14155551299", password="s3cretpass")
    assert user.phone == "+14155551299"
    assert user.phone_verified is False
