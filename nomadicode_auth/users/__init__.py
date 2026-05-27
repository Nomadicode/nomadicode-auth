"""Optional sub-app: a ready-to-use concrete User model.

Add to INSTALLED_APPS *only* if you want the default user::

    INSTALLED_APPS = [..., "nomadicode_auth", "nomadicode_auth.users"]
    AUTH_USER_MODEL = "nomadicode_auth_users.User"
"""

default_app_config = "nomadicode_auth.users.apps.NomadicodeAuthUsersConfig"
