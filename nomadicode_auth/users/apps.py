from django.apps import AppConfig


class NomadicodeAuthUsersConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "nomadicode_auth.users"
    label = "nomadicode_auth_users"
    verbose_name = "Nomadicode Auth — Users"
