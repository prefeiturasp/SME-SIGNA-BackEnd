from rest_framework import serializers
import re

class LoginSerializer(serializers.Serializer):
    username = serializers.CharField(required=True)
    password = serializers.CharField(required=True, write_only=True)

    def validate(self, attrs):
        username = attrs.get("username")

        digits = re.sub(r"\D", "", username or "")

        # valida RF (7 ou 8 dígitos)
        if len(digits) not in (7, 8):
            raise serializers.ValidationError({
                "username": "Login inválido. Informe RF (7 ou 8 dígitos)."
            })

        attrs["username"] = digits
        return attrs
