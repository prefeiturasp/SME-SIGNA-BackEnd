"""Testes para o serviço de senha."""

import pytest
from django.contrib.auth import get_user_model

from apps.helpers.exceptions import EmailNaoCadastradoError
from apps.usuarios.services.senha_service import SenhaService

User = get_user_model()


@pytest.mark.django_db
class TestSincronizarUsuarioLocal:
    """Testes para sincronizar_usuario_local."""

    def test_sincroniza_usuario_com_sucesso(self):
        """Verifica que o usuário é criado com os dados da SME."""
        user = SenhaService.sincronizar_usuario_local(
            "12345678",
            {
                "nome": "Fulano da Silva",
                "email": "fulano@example.com",
                "numeroDocumento": "12345678900",
            },
        )

        assert user.username == "12345678"
        assert user.name == "Fulano da Silva"
        assert user.email == "fulano@example.com"

    def test_sem_nome_retorna_usuario_existente_sem_sincronizar(self):
        """Verifica que sem nome nos dados SME, o usuário não é alterado."""
        User.objects.create_user(
            username="12345678", name="Nome Antigo", email="antigo@example.com"
        )

        user = SenhaService.sincronizar_usuario_local("12345678", {})

        assert user.name == "Nome Antigo"

    def test_conflito_de_email_gera_erro(self):
        """Verifica que e-mail duplicado gera EmailNaoCadastradoError."""
        User.objects.create_user(
            username="outro_usuario", email="duplicado@example.com"
        )

        with pytest.raises(EmailNaoCadastradoError):
            SenhaService.sincronizar_usuario_local(
                "12345678",
                {
                    "nome": "Fulano da Silva",
                    "email": "duplicado@example.com",
                    "numeroDocumento": "12345678900",
                },
            )
