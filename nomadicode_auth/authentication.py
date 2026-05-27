"""DRF authentication class that validates allauth.headless JWTs."""

from allauth.headless.tokens.strategies.jwt.internal import validate_access_token
from rest_framework.authentication import BaseAuthentication, get_authorization_header
from rest_framework.exceptions import AuthenticationFailed


class NomadicodeJWTAuthentication(BaseAuthentication):
    keyword = "Bearer"
    www_authenticate_realm = "api"

    def authenticate(self, request):
        auth = get_authorization_header(request).split()
        if not auth or auth[0].lower() != self.keyword.lower().encode():
            return None
        if len(auth) != 2:
            raise AuthenticationFailed("Invalid Authorization header.")
        try:
            token = auth[1].decode()
        except UnicodeError:
            raise AuthenticationFailed("Invalid Authorization header encoding.")

        result = validate_access_token(token)
        if result is None:
            raise AuthenticationFailed("Invalid or expired token.")
        user, _payload = result
        return user, token

    def authenticate_header(self, request):
        return f'{self.keyword} realm="{self.www_authenticate_realm}"'
