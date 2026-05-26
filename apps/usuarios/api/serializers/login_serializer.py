"""Serializers de autenticação de usuários.

Contém validações específicas para o login de usuários do sistema,
incluindo normalização do RF antes da autenticação.
"""

from rest_framework import serializers
import re


class LoginSerializer(serializers.Serializer):
    """Serializer para validação de credenciais de login.

    Valida o formato do nome de usuário e garante que a senha seja fornecida.
    """
    username = serializers.CharField(required=True)
    password = serializers.CharField(required=True, write_only=True)

    def validate(self, attrs):
        """Valida e normaliza o nome de usuário antes de autenticar.

        Args:
            attrs (dict): Dados enviados para autenticação.

        Returns:
            dict: Dados atualizados com o nome de usuário normalizado.

        Raises:
            serializers.ValidationError: Quando o RF não contém 7 ou 8 dígitos.
        """
        username = attrs.get("username")

        digits = re.sub(r"\D", "", username or "")

        # valida RF (7 ou 8 dígitos)
        if len(digits) not in (7, 8):
            raise serializers.ValidationError({
                "username": "Login inválido. Informe RF (7 ou 8 dígitos)."
            })

        attrs["username"] = digits
        return attrs
