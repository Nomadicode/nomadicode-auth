from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView

from ..serializers import SocialLoginSerializer
from ..services import SocialLoginFailed, login_with_provider_token
from ._common import APIError, token_response


class SocialLoginView(APIView):
    """POST /auth/social/<provider>/ — body: {access_token? id_token?}."""

    permission_classes = [AllowAny]
    authentication_classes: list = []

    def post(self, request, provider: str):
        ser = SocialLoginSerializer(data=request.data)
        ser.is_valid(raise_exception=True)
        try:
            user = login_with_provider_token(
                provider=provider,
                request=request,
                access_token=ser.validated_data.get("access_token") or None,
                id_token=ser.validated_data.get("id_token") or None,
            )
        except SocialLoginFailed as exc:
            raise APIError(str(exc), status_code=400, code="social_login_failed")
        return Response(token_response(user, request=request))
