"""Allauth adapters wired to package settings.

Projects can subclass these to customize behavior (e.g. copying extra
fields off a social profile). Point ``ACCOUNT_ADAPTER`` /
``SOCIALACCOUNT_ADAPTER`` at your subclass.
"""

from allauth.account.adapter import DefaultAccountAdapter
from allauth.socialaccount.adapter import DefaultSocialAccountAdapter

from .conf import frontend_url, settings as pkg_settings


class NomadicodeAccountAdapter(DefaultAccountAdapter):
    def is_open_for_signup(self, request):
        return True

    def get_email_confirmation_url(self, request, emailconfirmation):
        return frontend_url(
            pkg_settings.FRONTEND_EMAIL_CONFIRM_PATH, key=emailconfirmation.key
        )

    def format_email_subject(self, subject):
        prefix = pkg_settings.EMAIL_SUBJECT_PREFIX
        return f"{prefix}{subject}" if prefix else subject


class NomadicodeSocialAccountAdapter(DefaultSocialAccountAdapter):
    """Copies common profile fields from the social account into the user.

    Subclass + override ``populate_user`` for project-specific fields.
    """

    def save_user(self, request, sociallogin, form=None):
        user = super().save_user(request, sociallogin, form=form)
        extra = sociallogin.account.extra_data or {}

        changed = False
        if not user.first_name and (extra.get("given_name") or extra.get("first_name")):
            user.first_name = extra.get("given_name") or extra.get("first_name")
            changed = True
        if not user.last_name and (extra.get("family_name") or extra.get("last_name")):
            user.last_name = extra.get("family_name") or extra.get("last_name")
            changed = True
        if extra.get("picture") and hasattr(user, "profile_picture_url"):
            user.profile_picture_url = extra["picture"]
            changed = True
        # Social-verified emails are trusted.
        if user.email and hasattr(user, "email_verified") and not user.email_verified:
            user.email_verified = True
            changed = True
        if changed:
            user.save()
        return user
