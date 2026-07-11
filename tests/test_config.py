"""The NOMADICODE_AUTH dict is the single configuration surface:
defaults injection into Django settings + conf accessor precedence."""

from django.conf import settings as dj_settings
from django.test import SimpleTestCase, override_settings
from django.urls import NoReverseMatch, reverse

from nomadicode_auth.conf import settings as pkg_settings, sms_option


class DefaultsInjectionTests(SimpleTestCase):
    def test_account_settings_injected(self):
        self.assertIsNone(dj_settings.ACCOUNT_USER_MODEL_USERNAME_FIELD)
        self.assertEqual(dj_settings.ACCOUNT_LOGIN_METHODS, {"email"})
        self.assertEqual(dj_settings.ACCOUNT_SIGNUP_FIELDS, ["email*", "password1*"])
        self.assertEqual(dj_settings.ACCOUNT_EMAIL_VERIFICATION, "mandatory")
        self.assertEqual(
            dj_settings.ACCOUNT_ADAPTER,
            "nomadicode_auth.adapters.NomadicodeAccountAdapter",
        )
        self.assertEqual(
            dj_settings.SOCIALACCOUNT_ADAPTER,
            "nomadicode_auth.adapters.NomadicodeSocialAccountAdapter",
        )
        self.assertTrue(dj_settings.SOCIALACCOUNT_EMAIL_AUTHENTICATION)

    def test_headless_settings_injected(self):
        self.assertTrue(dj_settings.HEADLESS_ONLY)
        self.assertEqual(
            dj_settings.HEADLESS_TOKEN_STRATEGY,
            "nomadicode_auth.token_strategy.NomadicodeJWTTokenStrategy",
        )

    def test_jwt_ttls_mapped_from_nomadicode_auth(self):
        self.assertEqual(dj_settings.HEADLESS_JWT_ACCESS_TOKEN_EXPIRES_IN, 123)
        self.assertEqual(dj_settings.HEADLESS_JWT_REFRESH_TOKEN_EXPIRES_IN, 456)

    def test_project_defined_setting_wins(self):
        # tests/settings.py sets HEADLESS_JWT_ALGORITHM = "HS512"; the
        # package default (HS256) must not clobber it.
        self.assertEqual(dj_settings.HEADLESS_JWT_ALGORITHM, "HS512")

    def test_frontend_urls_built_from_frontend_url(self):
        urls = dj_settings.HEADLESS_FRONTEND_URLS
        self.assertEqual(
            urls["account_confirm_email"],
            "http://localhost:8080/auth/confirm-email/{key}",
        )
        self.assertIn("account_reset_password_from_key", urls)
        self.assertIn("socialaccount_login_error", urls)

    def test_socialaccount_providers_built_from_social(self):
        self.assertEqual(
            dj_settings.SOCIALACCOUNT_PROVIDERS,
            {"google": {"APP": {"client_id": "google-cid", "secret": "google-secret"}}},
        )


class ConfResolutionTests(SimpleTestCase):
    def test_sms_backend_from_sms_dict(self):
        self.assertEqual(
            pkg_settings.SMS_BACKEND, "nomadicode_auth.sms.dummy.DummyBackend"
        )

    @override_settings(NOMADICODE_AUTH={"SMS_BACKEND": "legacy.Backend"})
    def test_sms_backend_legacy_flat_key(self):
        self.assertEqual(pkg_settings.SMS_BACKEND, "legacy.Backend")

    @override_settings(
        SMS_BACKEND="toplevel.Backend",
        NOMADICODE_AUTH={"SMS_BACKEND": "legacy.Backend"},
    )
    def test_sms_backend_top_level_beats_flat_key(self):
        self.assertEqual(pkg_settings.SMS_BACKEND, "toplevel.Backend")

    @override_settings(NOMADICODE_AUTH={})
    def test_sms_backend_default(self):
        self.assertEqual(
            pkg_settings.SMS_BACKEND, "nomadicode_auth.sms.twilio.TwilioBackend"
        )

    def test_sms_option_from_sms_dict(self):
        self.assertEqual(sms_option("TWILIO_ACCOUNT_SID"), "sid-from-sms-dict")

    @override_settings(TWILIO_AUTH_TOKEN="top-level-token")
    def test_sms_option_falls_back_to_top_level_setting(self):
        self.assertEqual(sms_option("TWILIO_AUTH_TOKEN"), "top-level-token")
        self.assertEqual(sms_option("TWILIO_PHONE_FROM", "fallback"), "fallback")

    def test_social_providers_derived_from_social(self):
        self.assertEqual(pkg_settings.SOCIAL_PROVIDERS, ("google",))

    @override_settings(NOMADICODE_AUTH={"SOCIAL_PROVIDERS": ("apple",)})
    def test_social_providers_explicit_override(self):
        self.assertEqual(pkg_settings.SOCIAL_PROVIDERS, ("apple",))

    @override_settings(NOMADICODE_AUTH={})
    def test_social_providers_default(self):
        self.assertEqual(pkg_settings.SOCIAL_PROVIDERS, ("google", "facebook"))


class UrlMountingTests(SimpleTestCase):
    def test_enabled_provider_gets_social_endpoint(self):
        # SOCIAL only lists google, so only google is mounted.
        self.assertEqual(
            reverse("nomadicode_auth:social-google"), "/auth/social/google"
        )
        with self.assertRaises(NoReverseMatch):
            reverse("nomadicode_auth:social-facebook")
