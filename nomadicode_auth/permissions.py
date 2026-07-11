from rest_framework.permissions import BasePermission


class IsVerified(BasePermission):
    """User must have verified email or phone."""

    message = "Verify your email or phone before continuing."

    def has_permission(self, request, view):
        user = request.user
        return bool(
            user
            and user.is_authenticated
            and (
                getattr(user, "email_verified", False)
                or getattr(user, "phone_verified", False)
            )
        )


class IsEmailVerified(BasePermission):
    message = "Verify your email before continuing."

    def has_permission(self, request, view):
        user = request.user
        return bool(
            user and user.is_authenticated and getattr(user, "email_verified", False)
        )


class IsPhoneVerified(BasePermission):
    message = "Verify your phone before continuing."

    def has_permission(self, request, view):
        user = request.user
        return bool(
            user and user.is_authenticated and getattr(user, "phone_verified", False)
        )
