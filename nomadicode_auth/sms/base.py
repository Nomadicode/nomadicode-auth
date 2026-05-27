from dataclasses import dataclass


class SmsSendError(Exception):
    pass


@dataclass
class SmsMessage:
    to: str
    body: str
    from_: str | None = None


class BaseSmsBackend:
    """Subclass and implement ``send``.

    Backends should raise ``SmsSendError`` on transient/provider
    failures so the OTP service can surface a clean 502 to the client.
    """

    def send(self, *, to: str, body: str, from_: str | None = None) -> dict:
        raise NotImplementedError

    def send_message(self, message: SmsMessage) -> dict:
        return self.send(to=message.to, body=message.body, from_=message.from_)
