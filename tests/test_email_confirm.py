from allauth.account.models import EmailAddress, EmailConfirmationHMAC
from django.contrib.auth import get_user_model
from django.test import TestCase

from nomadicode_auth.services import AuthError, confirm_email_key

User = get_user_model()


class ConfirmEmailKeyTests(TestCase):
    def test_confirm_without_request_uses_stub(self):
        # Out-of-request usage (shell, background task) must not require
        # an HttpRequest with messages middleware.
        user = User.objects.create_user(email="a@b.com", password="S3cure-pass!")
        address = EmailAddress.objects.create(
            user=user, email=user.email, verified=False, primary=True
        )
        key = EmailConfirmationHMAC(address).key

        confirmed = confirm_email_key(key)

        self.assertEqual(confirmed, user)
        address.refresh_from_db()
        user.refresh_from_db()
        self.assertTrue(address.verified)
        self.assertTrue(user.email_verified)

    def test_invalid_key_raises(self):
        with self.assertRaises(AuthError):
            confirm_email_key("not-a-real-key")
