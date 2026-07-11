# nomadicode-auth

Batteries-included Django auth on top of [django-allauth]:

- Email or phone signup + login, with email/phone verification gates
- JWTs (allauth.headless strategy) — `Bearer` tokens, refresh + rotation
- Google + Facebook login by access/id token (mobile-friendly)
- Pluggable SMS backends (`SMS_BACKEND = "..."`) — Twilio by default
- Clean, predictable REST URLs — mount under any prefix you want

## Install

```bash
pip install nomadicode-auth          # core
pip install nomadicode-auth[twilio]  # if you want the Twilio SMS backend
```

## 1. Settings

```python
INSTALLED_APPS = [
    # ... your apps
    "django.contrib.sites",

    # allauth (required)
    "allauth",
    "allauth.account",
    "allauth.socialaccount",
    "allauth.socialaccount.providers.google",
    "allauth.socialaccount.providers.facebook",
    "allauth.headless",

    "rest_framework",
    "nomadicode_auth",

    # Optional: ship with the default User model.
    # Skip this if you want to bring your own User
    # (subclass nomadicode_auth.models.AbstractNomadicodeUser).
    "nomadicode_auth.users",
]

SITE_ID = 1

AUTH_USER_MODEL = "nomadicode_auth_users.User"   # only if you installed the .users subapp

MIDDLEWARE += ["allauth.account.middleware.AccountMiddleware"]

AUTHENTICATION_BACKENDS = (
    "django.contrib.auth.backends.ModelBackend",
    "allauth.account.auth_backends.AuthenticationBackend",
)

# DRF: validate the JWTs nomadicode-auth issues.
REST_FRAMEWORK = {
    "DEFAULT_AUTHENTICATION_CLASSES": (
        "nomadicode_auth.authentication.NomadicodeJWTAuthentication",
    ),
    "DEFAULT_PERMISSION_CLASSES": ("rest_framework.permissions.IsAuthenticated",),
}

# Package configuration — the ONLY block you need. Everything has a
# sensible default; an empty dict works for dev.
NOMADICODE_AUTH = {
    "FRONTEND_URL": os.environ["FRONTEND_URL"],          # e.g. https://app.example.com
    "REQUIRE_VERIFIED_EMAIL": True,
    "REQUIRE_VERIFIED_PHONE": True,
    "JWT_ACCESS_TTL": 60 * 60,
    "JWT_REFRESH_TTL": 60 * 60 * 24 * 7,
    "JWT_ALGORITHM": "HS256",   # signs with SECRET_KEY; switch to RS256 if you need external verification

    # SMS — Twilio by default. Swap BACKEND for any registered backend;
    # backend options live right here too.
    "SMS": {
        "BACKEND": "nomadicode_auth.sms.twilio.TwilioBackend",
        "TWILIO_ACCOUNT_SID": os.environ["TWILIO_ACCOUNT_SID"],
        "TWILIO_AUTH_TOKEN": os.environ["TWILIO_AUTH_TOKEN"],
        "TWILIO_PHONE_FROM": os.environ["TWILIO_PHONE_FROM"],
    },

    # Social login — providers listed here get a /auth/social/<provider>/
    # endpoint and their credentials are wired into allauth automatically
    # (no SocialApp rows, no SOCIALACCOUNT_PROVIDERS).
    "SOCIAL": {
        "google":   {"client_id": os.environ["GOOGLE_CLIENT_ID"], "secret": os.environ["GOOGLE_CLIENT_SECRET"]},
        "facebook": {"client_id": os.environ["FACEBOOK_APP_ID"],  "secret": os.environ["FACEBOOK_APP_SECRET"]},
    },
}
```

That's it. At startup the package injects the allauth account/headless
settings it needs (`ACCOUNT_*`, `HEADLESS_*`, `SOCIALACCOUNT_*`) with
correct defaults — email login, mandatory verification when
`REQUIRE_VERIFIED_EMAIL`, the package adapters and JWT token strategy,
and `SOCIALACCOUNT_PROVIDERS` built from `"SOCIAL"`. Define any of those
settings yourself in `settings.py` and your value wins.

## 2. URLs

```python
# urls.py
from django.urls import include, path

urlpatterns = [
    path("auth/", include("nomadicode_auth.urls")),
    path("accounts/", include("allauth.urls")),   # required by allauth even in headless mode
]
```

## 3. Migrate

```bash
python manage.py migrate
```

## 4. Endpoints

All endpoints live under whatever prefix you mounted (`/auth/` in the example).

| Method  | Path                      | Body                                                             |
| ------- | ------------------------- | ---------------------------------------------------------------- |
| `POST`  | `/signup`                 | `{email, password, ...}` _or_ `{phone, password, otp_code, ...}` |
| `POST`  | `/login`                  | `{identifier, password}` (email or phone)                        |
| `POST`  | `/logout`                 | —                                                                |
| `POST`  | `/refresh`                | `{refresh}`                                                      |
| `GET`   | `/me`                     | (auth)                                                           |
| `PATCH` | `/me`                     | `{first_name?, last_name?, ...}`                                 |
| `POST`  | `/verify-email`           | `{key}`                                                          |
| `POST`  | `/verify-email/resend`    | `{email}`                                                        |
| `POST`  | `/verify-phone/send`      | `{phone, channel?}`                                              |
| `POST`  | `/verify-phone`           | `{phone, code}`                                                  |
| `POST`  | `/password/reset`         | `{email}`                                                        |
| `POST`  | `/password/reset/confirm` | `{key, new_password}`                                            |
| `POST`  | `/password/change`        | `{old_password, new_password}`                                   |
| `POST`  | `/social/google`          | `{id_token}` _or_ `{access_token}`                               |
| `POST`  | `/social/facebook`        | `{access_token}`                                                 |

Successful auth endpoints return:

```json
{
  "access":  "eyJ...",
  "refresh": "eyJ...",
  "user":    { "id": "...", "email": "...", "phone": null, "email_verified": true, ... }
}
```

## 5. Phone signup flow

```
POST /auth/verify-phone/send          { "phone": "+14155551234" }
  → 202 { "detail": "Code sent." }

POST /auth/signup                     { "phone": "+14155551234", "password": "...", "otp_code": "123456" }
  → 201 { "access": "...", "refresh": "...", "user": {...} }
```

Phone signups are auto-verified — possessing the OTP proves ownership.

## 6. Email signup flow

```
POST /auth/signup                     { "email": "a@b.com", "password": "..." }
  → 201 { "detail": "Check your email", "user": {...} }
# user receives an email containing FRONTEND_URL + FRONTEND_EMAIL_CONFIRM_PATH (key substituted)

POST /auth/verify-email               { "key": "<key from URL>" }
  → 200 { "access": "...", "refresh": "...", "user": {...} }
```

## 7. SMS backends

Built-in:

| Path                                                 | Notes                                                                             |
| ---------------------------------------------------- | --------------------------------------------------------------------------------- |
| `nomadicode_auth.sms.twilio.TwilioBackend`           | Default. Requires `pip install nomadicode-auth[twilio]` + `TWILIO_*` SMS options. |
| `nomadicode_auth.sms.console.ConsoleBackend`         | Logs to stdout — great for dev.                                                   |
| `nomadicode_auth.sms.dummy.DummyBackend`             | No-op, records to `DummyBackend.sent` — use in tests.                             |
| `nomadicode_auth.sms.messagebird.MessageBirdBackend` | Example second provider.                                                          |

### Writing a custom backend

```python
# myproject/sms/vonage.py
from nomadicode_auth.sms import BaseSmsBackend, SmsSendError

class VonageBackend(BaseSmsBackend):
    def __init__(self):
        ...

    def send(self, *, to, body, from_=None):
        try:
            return self._client.send({"to": to, "from": from_, "text": body})
        except VonageError as exc:
            raise SmsSendError(str(exc)) from exc
```

```python
# settings.py
NOMADICODE_AUTH = {
    ...,
    "SMS": {"BACKEND": "myproject.sms.vonage.VonageBackend"},
}
```

## 8. Adding a social provider

1. Install the allauth provider app (e.g. `allauth.socialaccount.providers.apple`).
2. Add its credentials under `NOMADICODE_AUTH["SOCIAL"]` (or add a `SocialApp` row via admin/fixture instead).
3. Register a verifier:

```python
# myproject/social.py
from nomadicode_auth.services.social import register_verifier, SocialLoginFailed
import requests

@register_verifier("apple")
def verify_apple(*, id_token, **_):
    # verify against https://appleid.apple.com/auth/keys, then:
    return {
        "uid": claims["sub"],
        "email": claims.get("email"),
        "first_name": "",
        "last_name": "",
        "picture": None,
        "extra": claims,
    }
```

```python
# settings.py
NOMADICODE_AUTH = {
    ...,
    "SOCIAL": {
        "google":   {"client_id": "...", "secret": "..."},
        "facebook": {"client_id": "...", "secret": "..."},
        "apple":    {"client_id": "...", "secret": "..."},
    },
}
```

Ensure your code imports `myproject.social` at startup (e.g. from your app's `ready()`).

## 9. Bring your own User model

Skip `"nomadicode_auth.users"` in `INSTALLED_APPS`, then:

```python
# myproject/users/models.py
from nomadicode_auth.models import AbstractNomadicodeUser

class User(AbstractNomadicodeUser):
    organization = models.ForeignKey("orgs.Organization", on_delete=models.CASCADE, null=True)

    class Meta(AbstractNomadicodeUser.Meta):
        abstract = False
```

```python
# settings.py
AUTH_USER_MODEL = "users.User"
```

Run `makemigrations users && migrate`.

## 10. Verification helpers

```python
from nomadicode_auth.permissions import IsVerified, IsEmailVerified, IsPhoneVerified

class MyView(APIView):
    permission_classes = [IsAuthenticated, IsVerified]
```

## License

MIT
