"""Logs SMS messages to stdout — use in dev so you can see OTP codes."""

import logging

from .base import BaseSmsBackend

logger = logging.getLogger("nomadicode_auth.sms")


class ConsoleBackend(BaseSmsBackend):
    def send(self, *, to: str, body: str, from_: str | None = None) -> dict:
        logger.info("[SMS] to=%s from=%s body=%s", to, from_ or "-", body)
        print(f"[SMS] to={to} from={from_ or '-'} body={body}")
        return {"sid": "console", "status": "delivered", "to": to}
