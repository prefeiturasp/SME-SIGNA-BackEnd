"""Testes do serializer de redefinição de senha.

Este módulo valida a lógica do serializer RedefinirSenhaSerializer,
incluindo validação de dados, correspondência de senhas e verificação de
UID e token.
"""

import pytest

from django.contrib.auth import get_user_model
from django.contrib.auth.tokens import default_token_generator
from django.utils.encoding import force_bytes
from django.utils.http import urlsafe_base64_encode

from apps.usuarios.api.serializers.senha_serializer import (
    RedefinirSenhaSerializer,
)

User = get_user_model()


@pytest.mark.django_db
class TestRedefinirSenhaSerializer:
    """Testa o serializer de redefinição de senha.

    Verifica os casos de validação válidos e inválidos para o fluxo de
    redefinição de senha.
    """

    def test_serializer_valid_data(self, django_user_model):
        """Verifica que dados válidos são aceitos pelo serializer."""
        user = django_user_model.objects.create_user(
            username="usuario", password="Senha@123"
        )

        uid = urlsafe_base64_encode(force_bytes(user.pk))
        token = default_token_generator.make_token(user)

        data = {
            "uid": uid,
            "token": token,
            "new_pass": "NovaSenha@123",
            "new_pass_confirm": "NovaSenha@123",
        }

        serializer = RedefinirSenhaSerializer(data=data)

        assert serializer.is_valid(), serializer.errors

        validated_data = serializer.validated_data

        assert validated_data["user"] == user
        assert validated_data["new_pass"] == "NovaSenha@123"
        assert "uid" not in validated_data
        assert "new_pass_confirm" not in validated_data

    def test_serializer_password_mismatch(self, django_user_model):
        """Verifica que senhas divergentes geram erro de validação."""
        user = django_user_model.objects.create_user(
            username="usuario", password="Senha@123"
        )

        uid = urlsafe_base64_encode(force_bytes(user.pk))
        token = default_token_generator.make_token(user)

        data = {
            "uid": uid,
            "token": token,
            "new_pass": "Senha1@123",
            "new_pass_confirm": "Senha2@123",
        }

        serializer = RedefinirSenhaSerializer(data=data)

        assert not serializer.is_valid()
        assert (
            serializer.errors["non_field_errors"][0]
            == "As senhas não conferem."
        )

    def test_serializer_user_not_found(self):
        """Verifica que UID inexistente resulta em erro de usuário não encontrado."""
        uid = urlsafe_base64_encode(force_bytes(99999))

        data = {
            "uid": uid,
            "token": "token",
            "new_pass": "Senha@123",
            "new_pass_confirm": "Senha@123",
        }

        serializer = RedefinirSenhaSerializer(data=data)

        assert not serializer.is_valid()
        assert (
            serializer.errors["non_field_errors"][0]
            == "Usuário não encontrado."
        )

    def test_serializer_invalid_token(self, django_user_model):
        """Verifica que token inválido ou expirado é rejeitado."""
        user = django_user_model.objects.create_user(
            username="usuario", password="Senha@123"
        )

        uid = urlsafe_base64_encode(force_bytes(user.pk))

        data = {
            "uid": uid,
            "token": "token-invalido",
            "new_pass": "Senha@123",
            "new_pass_confirm": "Senha@123",
        }

        serializer = RedefinirSenhaSerializer(data=data)

        assert not serializer.is_valid()
        assert (
            serializer.errors["non_field_errors"][0]
            == "Token inválido ou expirado."
        )

    def test_serializer_invalid_uid(self):
        """Verifica que UID malformado gera erro de validação."""
        data = {
            "uid": "uid-invalido",
            "token": "token",
            "new_pass": "Senha@123",
            "new_pass_confirm": "Senha@123",
        }

        serializer = RedefinirSenhaSerializer(data=data)

        assert not serializer.is_valid()
        assert (
            serializer.errors["non_field_errors"][0]
            == "UID inválido ou malformado."
        )

    def test_serializer_uid_not_numeric(self, django_user_model):
        """
        UID decodificado não numérico deve retornar uid_invalid
        """
        user = django_user_model.objects.create_user(
            username="teste", password="Senha@123"
        )

        uid = urlsafe_base64_encode(force_bytes("abc"))
        token = default_token_generator.make_token(user)

        data = {
            "uid": uid,
            "token": token,
            "new_pass": "NovaSenha@123",
            "new_pass_confirm": "NovaSenha@123",
        }

        serializer = RedefinirSenhaSerializer(data=data)

        assert serializer.is_valid() is False
        assert "uid_invalid" in str(serializer.errors)
