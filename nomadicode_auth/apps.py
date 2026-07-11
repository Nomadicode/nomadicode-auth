from django.apps import AppConfig


class NomadicodeAuthConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "nomadicode_auth"
    label = "nomadicode_auth"
    verbose_name = "Nomadicode Auth"

    def ready(self):
        from .defaults import apply_default_settings

        apply_default_settings()

        from . import signals  # noqa: F401
