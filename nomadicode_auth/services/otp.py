"""Phone OTP orchestration on top of the OTPCode model + SMS backend."""

from django.template.loader import render_to_string

from ..conf import settings as pkg_settings
from ..models import OTPChannel, OTPCode, OTPPurpose
from ..sms import SmsSendError, get_sms_backend


class OTPRateLimited(Exception):
    pass


class OTPVerificationFailed(Exception):
    pass


def _render_body(code: str, purpose: str) -> str:
    return render_to_string(
        "nomadicode_auth/sms/otp.txt", {"code": code, "purpose": purpose}
    ).strip()


def send_phone_otp(
    *,
    phone: str,
    purpose: str = OTPPurpose.VERIFY_PHONE,
    channel: str = OTPChannel.SMS,
) -> OTPCode:
    if OTPCode.recent_request_count(phone=phone) >= pkg_settings.OTP_RATE_LIMIT_PER_HOUR:
        raise OTPRateLimited("Too many OTP requests; try again later.")

    row, code = OTPCode.issue(phone=phone, purpose=purpose, channel=channel)
    backend = get_sms_backend()
    try:
        backend.send(to=phone, body=_render_body(code, purpose))
    except SmsSendError:
        # Roll back so the rate limiter doesn't count failed sends.
        row.delete()
        raise
    return row


def verify_phone_otp(*, phone: str, code: str, purpose: str = OTPPurpose.VERIFY_PHONE) -> bool:
    ok = OTPCode.verify(phone=phone, purpose=purpose, code=code)
    if not ok:
        raise OTPVerificationFailed("Invalid or expired code.")
    return True
