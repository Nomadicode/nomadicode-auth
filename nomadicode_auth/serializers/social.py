from rest_framework import serializers


class SocialLoginSerializer(serializers.Serializer):
    access_token = serializers.CharField(required=False, allow_blank=True)
    id_token = serializers.CharField(required=False, allow_blank=True)

    def validate(self, attrs):
        if not attrs.get("access_token") and not attrs.get("id_token"):
            raise serializers.ValidationError("access_token or id_token is required.")
        return attrs
