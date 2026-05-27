"""Abstract user with email + phone + verification flags.

Projects either:
  1. Use the ready-made concrete model — add ``nomadicode_auth.users`` to
     INSTALLED_APPS and set ``AUTH_USER_MODEL = "nomadicode_auth_users.User"``.
  2. Or subclass ``AbstractNomadicodeUser`` in their own app to add custom
     fields.
"""

from django.contrib.auth.base_user import AbstractBaseUser, BaseUserManager
from django.contrib.auth.models import PermissionsMixin
from django.db import models
from django.utils import timezone


class NomadicodeUserManager(BaseUserManager):
    use_in_migrations = True

    def create_user(self, email=None, phone=None, password=None, **extra):
        if not email and not phone:
            raise ValueError("Either email or phone must be provided.")
        if email:
            email = self.normalize_email(email)
        user = self.model(email=email, phone=phone, **extra)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email=None, phone=None, password=None, **extra):
        extra.setdefault("is_staff", True)
        extra.setdefault("is_superuser", True)
        if not extra.get("is_staff"):
            raise ValueError("Superuser must have is_staff=True.")
        if not extra.get("is_superuser"):
            raise ValueError("Superuser must have is_superuser=True.")
        return self.create_user(email=email, phone=phone, password=password, **extra)


class AbstractNomadicodeUser(AbstractBaseUser, PermissionsMixin):
    first_name = models.CharField(max_length=128, blank=True)
    last_name = models.CharField(max_length=128, blank=True)
    email = models.EmailField(max_length=512, null=True, blank=True, unique=True)
    phone = models.CharField(max_length=48, null=True, blank=True, unique=True)
    email_verified = models.BooleanField(default=False)
    phone_verified = models.BooleanField(default=False)
    is_staff = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)
    date_joined = models.DateTimeField(default=timezone.now)

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS: list[str] = []

    objects = NomadicodeUserManager()

    class Meta:
        abstract = True

    def __str__(self):
        return self.email or self.phone or f"user:{self.pk}"

    def get_full_name(self) -> str:
        return f"{self.first_name} {self.last_name}".strip()

    def get_short_name(self) -> str:
        return self.first_name or self.email or self.phone or ""

    @property
    def is_verified(self) -> bool:
        """True if the user has verified at least one identifier."""
        return self.email_verified or self.phone_verified
