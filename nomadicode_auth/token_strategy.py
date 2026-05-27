"""JWT strategy that adds a ``user_id`` claim alongside allauth's ``sub``.

simplejwt-derived consumers (channels middleware, etc.) typically read
``user_id``; allauth's default only emits ``sub``. Including both
keeps both worlds happy.
"""

from allauth.headless.tokens.strategies.jwt import JWTTokenStrategy


class NomadicodeJWTTokenStrategy(JWTTokenStrategy):
    def get_claims(self, user):
        return {"user_id": str(user.pk)}
