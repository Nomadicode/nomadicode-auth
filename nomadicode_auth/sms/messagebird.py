"""MessageBird SMS backend — example second provider.

Reads:
    MESSAGEBIRD_ACCESS_KEY
    MESSAGEBIRD_ORIGINATOR  (default sender id / number, optional if you pass from_)
"""

import json

import requests
from django.conf import settings as django_settings

from .base import BaseSmsBackend, SmsSendError

API_URL = "https://rest.messagebird.com/messages"


class MessageBirdBackend(BaseSmsBackend):
    def __init__(self):
        self._key = getattr(django_settings, "MESSAGEBIRD_ACCESS_KEY", "")
        if not self._key:
            raise SmsSendError("MESSAGEBIRD_ACCESS_KEY must be set.")
        self._default_from = getattr(django_settings, "MESSAGEBIRD_ORIGINATOR", "") or None

    def send(self, *, to: str, body: str, from_: str | None = None) -> dict:
        sender = from_ or self._default_from
        if not sender:
            raise SmsSendError("No sender — set MESSAGEBIRD_ORIGINATOR or pass from_=.")

        try:
            resp = requests.post(
                API_URL,
                headers={
                    "Authorization": f"AccessKey {self._key}",
                    "Content-Type": "application/json",
                },
                data=json.dumps({"originator": sender, "recipients": [to], "body": body}),
                timeout=10,
            )
            resp.raise_for_status()
        except requests.RequestException as exc:
            raise SmsSendError(str(exc)) from exc

        payload = resp.json()
        return {"sid": payload.get("id"), "status": "queued", "to": to}
