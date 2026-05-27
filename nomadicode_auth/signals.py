"""Wire allauth signals to the package's verification state."""

from allauth.account.signals import email_confirmed
from django.dispatch import receiver


@receiver(email_confirmed)
def _mark_email_verified(sender, request, email_address, **kwargs):
    user = email_address.user
    if hasattr(user, "email_verified") and not user.email_verified:
        user.email_verified = True
        user.save(update_fields=["email_verified"])
