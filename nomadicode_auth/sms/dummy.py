"""No-op SMS backend — use in tests where you don't care what was sent."""

from .base import BaseSmsBackend


class DummyBackend(BaseSmsBackend):
    sent: list[dict] = []

    def send(self, *, to: str, body: str, from_: str | None = None) -> dict:
        record = {"to": to, "body": body, "from_": from_}
        self.__class__.sent.append(record)
        return {"sid": "dummy", "status": "queued", "to": to}
