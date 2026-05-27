"""SMS backend loader — mirrors Django's EMAIL_BACKEND pattern.

Usage::

    # settings.py
    SMS_BACKEND = "nomadicode_auth.sms.twilio.TwilioBackend"

    # anywhere
    from nomadicode_auth.sms import get_sms_backend
    get_sms_backend().send(to="+15555550100", body="Your code is 123456")

Write a custom backend by subclassing ``BaseSmsBackend``.
"""

from django.utils.module_loading import import_string

from ..conf import settings
from .base import BaseSmsBackend, SmsMessage, SmsSendError

__all__ = [
    "BaseSmsBackend",
    "SmsMessage",
    "SmsSendError",
    "get_sms_backend",
]


def get_sms_backend(path: str | None = None) -> BaseSmsBackend:
    cls = import_string(path or settings.SMS_BACKEND)
    return cls()
