"""Twilio SMS backend.

Reads (from ``NOMADICODE_AUTH["SMS"]``, falling back to top-level
Django settings of the same name):
    TWILIO_ACCOUNT_SID
    TWILIO_AUTH_TOKEN
    TWILIO_PHONE_FROM     (default sender, optional if you pass ``from_=``)
    TWILIO_MESSAGING_SERVICE_SID  (optional; preferred over a from-number when set)

Install with: ``pip install nomadicode-auth[twilio]``
"""

from ..conf import sms_option
from .base import BaseSmsBackend, SmsSendError


class TwilioBackend(BaseSmsBackend):
    def __init__(self):
        try:
            from twilio.rest import Client
        except ImportError as exc:
            raise ImportError(
                "TwilioBackend requires the 'twilio' package — "
                "install with `pip install nomadicode-auth[twilio]`."
            ) from exc

        sid = sms_option("TWILIO_ACCOUNT_SID")
        token = sms_option("TWILIO_AUTH_TOKEN")
        if not sid or not token:
            raise SmsSendError("TWILIO_ACCOUNT_SID and TWILIO_AUTH_TOKEN must be set.")
        self._client = Client(sid, token)
        self._default_from = sms_option("TWILIO_PHONE_FROM") or None
        self._messaging_service_sid = sms_option("TWILIO_MESSAGING_SERVICE_SID") or None

    def send(self, *, to: str, body: str, from_: str | None = None) -> dict:
        kwargs = {"to": to, "body": body}
        if self._messaging_service_sid:
            kwargs["messaging_service_sid"] = self._messaging_service_sid
        else:
            sender = from_ or self._default_from
            if not sender:
                raise SmsSendError(
                    "No sender configured. Set TWILIO_PHONE_FROM or "
                    "TWILIO_MESSAGING_SERVICE_SID, or pass from_=."
                )
            kwargs["from_"] = sender

        try:
            msg = self._client.messages.create(**kwargs)
        except Exception as exc:
            raise SmsSendError(str(exc)) from exc

        return {"sid": msg.sid, "status": msg.status, "to": to}
