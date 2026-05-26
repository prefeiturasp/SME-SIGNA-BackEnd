"""Serializer para recuperação de informações do usuário autenticado.

Este módulo expõe apenas os campos de perfil necessários para a rota
"me" do endpoint de usuários.
"""

from rest_framework import serializers
from django.contrib.auth import get_user_model

User = get_user_model()


class UserMeSerializer(serializers.ModelSerializer):
    """Serializer do usuário atual.

    Retorna os campos públicos do perfil do usuário autenticado.
    """
    class Meta:
        model = User
        fields = (
            "username",
            "name",
            "email",
            "cpf",
        )

