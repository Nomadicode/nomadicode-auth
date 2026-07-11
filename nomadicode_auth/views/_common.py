"""Shared response shape + a tiny helper to wrap a user as a token payload."""

from rest_framework import status
from rest_framework.exceptions import APIException

from ..serializers import UserMeSerializer
from ..tokens import issue_jwt_for_user


def token_response(user, *, request=None) -> dict:
    access, refresh = issue_jwt_for_user(user)
    return {
        "access": access,
        "refresh": refresh,
        "user": UserMeSerializer(user, context={"request": request}).data,
    }


class APIError(APIException):
    """Raises a 400 with a clean ``{"detail": "..."}`` shape from a string."""

    status_code = status.HTTP_400_BAD_REQUEST
    default_detail = "Bad request."
    default_code = "bad_request"

    def __init__(
        self, message: str, *, code: str | None = None, status_code: int | None = None
    ):
        if status_code is not None:
            self.status_code = status_code
        super().__init__(detail=message, code=code or self.default_code)
