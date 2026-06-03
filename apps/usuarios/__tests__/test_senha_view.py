"""Testes das views e serializers de senha.

Este módulo contém testes para os endpoints e funcionalidades de recuperação,
redefinição e atualização de senha no pacote de usuários.
"""

import os
import secrets
from unittest.mock import MagicMock, patch

import pytest

from django.contrib.auth import get_user_model
from django.contrib.auth.tokens import default_token_generator
from django.db import IntegrityError
from django.test import TestCase
from django.utils.encoding import force_bytes
from django.utils.http import urlsafe_base64_encode
from rest_framework import serializers, status
from rest_framework.test import APIClient, APIRequestFactory

from apps.helpers.exceptions import SmeIntegracaoError
from apps.usuarios.api.views.senha_view import (
    AtualizarSenhaSerializer,
    AtualizarSenhaViewSet,
    EsqueciMinhaSenhaViewSet,
    RedefinirSenhaViewSet,
)

User = get_user_model()


@pytest.fixture
def view():
    """Retorna a instância da view de atualização de senha para testes."""
    return AtualizarSenhaViewSet()


@pytest.fixture
def mock_request():
    """Cria um request mockado com usuário autenticado falso."""
    request = MagicMock()
    request.user = MagicMock()
    request.user.username = "testuser"
    request.user.check_password.return_value = True
    request.user.id = 1
    return request


class TestEsqueciMinhaSenhaViewSet(TestCase):
    """Testa o fluxo de recuperação de senha via EsqueciMinhaSenhaViewSet.

    Cobre os casos de envio de e-mail de redefinição, tratamento de erros
    e criação/atualização de usuário local a partir de dados SME.
    """

    @classmethod
    def setUpClass(cls):
        """Configura variáveis globais necessárias para os testes."""
        super().setUpClass()
        os.environ["AMBIENTE_URL"] = "http://testserver"

    def setUp(self):
        """Inicializa cliente, usuário e dados padrão para os testes."""
        self.client = APIClient()
        self.url = "/api/usuario/esqueci-senha"

        User.objects.all().delete()

        self.user = User.objects.create_user(
            username="1234567", email="usuario@teste.com", name="Usuário Teste"
        )

        self.valid_data = {"username": "1234567"}

    def tearDown(self):
        """Remove dados criados durante os testes."""
        User.objects.all().delete()

    @patch(
        "apps.usuarios.api.views.senha_view.SmeIntegracaoService.informacao_usuario_sgp"
    )
    @patch(
        "apps.usuarios.api.views.senha_view.SenhaService.gerar_token_para_reset"
    )
    @patch("apps.usuarios.api.views.senha_view.EnviaEmailService.enviar")
    @patch("apps.usuarios.api.views.senha_view.env")
    def test_post_success_local_user_with_email(
        self, mock_env, mock_enviar, mock_gerar_token, mock_informacao_usuario
    ):
        """Testa fluxo normal onde usuário existe localmente e tem email"""
        mock_env.return_value = "http://localhost:8000"
        mock_informacao_usuario.return_value = {
            "email": "usuario@teste.com",
            "nome": "Usuário Teste",
            "numeroDocumento": "12345678900",
        }
        mock_gerar_token.return_value = {
            "uid": "test-uid",
            "token": "test-token",
            "name": "Usuário",
        }
        response = self.client.post(self.url, self.valid_data, format="json")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("Enviamos um link", response.data["detail"])

        mock_gerar_token.assert_called_once_with(
            "1234567", "usuario@teste.com"
        )
        mock_enviar.assert_called_once()

    @patch(
        "apps.usuarios.api.views.senha_view.SmeIntegracaoService.informacao_usuario_sgp"
    )
    @patch(
        "apps.usuarios.api.views.senha_view.SenhaService.gerar_token_para_reset"
    )
    @patch("apps.usuarios.api.views.senha_view.EnviaEmailService.enviar")
    @patch("apps.usuarios.api.views.senha_view.env")
    def test_post_success_local_user_with_short_email(
        self, mock_env, mock_enviar, mock_gerar_token, mock_informacao_usuario
    ):
        """Testa fluxo com email curto para verificar anonimização"""
        mock_env.return_value = "http://localhost:8000"
        mock_informacao_usuario.return_value = {"email": "us@teste.com"}
        mock_gerar_token.return_value = {
            "uid": "test-uid",
            "token": "test-token",
            "name": "Usuário",
        }
        response = self.client.post(self.url, self.valid_data, format="json")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("Enviamos um link", response.data["detail"])
        self.assertIn("u*@teste.com", response.data["detail"])

        mock_gerar_token.assert_called_once_with("1234567", "us@teste.com")
        mock_enviar.assert_called_once()

    @patch(
        "apps.usuarios.api.views.senha_view.SmeIntegracaoService.informacao_usuario_sgp"
    )
    @patch(
        "apps.usuarios.api.views.senha_view.SenhaService.gerar_token_para_reset"
    )
    @patch("apps.usuarios.api.views.senha_view.EnviaEmailService.enviar")
    @patch("apps.usuarios.api.views.senha_view.env")
    def test_post_success_api_email(
        self, mock_env, mock_enviar, mock_gerar_token, mock_informacao_usuario
    ):
        """Testa fluxo onde usuário existe localmente mas email vem da API"""
        User.objects.create_user(
            username="7654321", email="", name="Usuário Sem Email"
        )

        mock_env.return_value = "http://localhost:8000"
        mock_informacao_usuario.return_value = {"email": "novo@api.com"}
        mock_gerar_token.return_value = {
            "uid": "test-uid",
            "token": "test-token",
            "name": "Usuário",
        }

        response = self.client.post(
            self.url, {"username": "7654321"}, format="json"
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        mock_informacao_usuario.assert_called_once_with("7654321")

    @patch(
        "apps.usuarios.api.views.senha_view.SmeIntegracaoService.informacao_usuario_sgp"
    )
    def test_post_user_not_found(self, mock_sme):
        """Usuário não existe nem local nem SME"""

        mock_sme.return_value = None

        response = self.client.post(
            self.url, {"username": "9999999"}, format="json"
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data["detail"], "Usuário não encontrado")

    @patch(
        "apps.usuarios.api.views.senha_view.SmeIntegracaoService.informacao_usuario_sgp"
    )
    def test_post_email_not_found_anywhere(self, mock_informacao_usuario):
        """Testa quando email não é encontrado nem na API nem localmente"""
        User.objects.create_user(
            username="1111111", email="", name="Usuário Sem Email"
        )

        mock_informacao_usuario.return_value = {}

        response = self.client.post(
            self.url, {"username": "1111111"}, format="json"
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("E-mail não encontrado!", response.data["detail"])

    def test_post_invalid_data(self):
        """Testa com dados inválidos (username muito curto)"""
        invalid_data = {"username": "123"}

        response = self.client.post(self.url, invalid_data, format="json")

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data["detail"], "Usuário não encontrado")

    @patch(
        "apps.usuarios.api.views.senha_view.SmeIntegracaoService.informacao_usuario_sgp"
    )
    def test_post_api_external_failure(self, mock_informacao_usuario):
        """Testa quando a API externa falha mas usuário tem email local"""
        mock_informacao_usuario.side_effect = Exception("API Error")

        response = self.client.post(self.url, self.valid_data, format="json")

        self.assertEqual(response.status_code, status.HTTP_200_OK)

    @patch("apps.usuarios.api.views.senha_view.User.objects.filter")
    def test_post_unexpected_exception(self, mock_filter):
        """Testa tratamento de exceção inesperada"""
        mock_filter.side_effect = Exception("Database Error")

        response = self.client.post(self.url, self.valid_data, format="json")

        self.assertEqual(
            response.status_code, status.HTTP_500_INTERNAL_SERVER_ERROR
        )
        self.assertEqual(response.data["detail"], "Erro interno no servidor.")

    @patch(
        "apps.usuarios.api.views.senha_view.SenhaService.gerar_token_para_reset"
    )
    @patch("apps.usuarios.api.views.senha_view.EnviaEmailService.enviar")
    @patch("apps.usuarios.api.views.senha_view.env")
    @patch("apps.usuarios.api.views.senha_view.anonimizar_email")
    def test_processar_envio_email_method(
        self, mock_anonimizar, mock_env, mock_enviar, mock_gerar_token
    ):
        """Testa o método privado _processar_envio_email diretamente"""
        mock_env.return_value = "http://localhost:8000"
        mock_gerar_token.return_value = {
            "uid": "test-uid",
            "token": "test-token",
            "name": "Usuário",
        }
        mock_anonimizar.return_value = "u***@teste.com"

        view = EsqueciMinhaSenhaViewSet()

        response = view._processar_envio_email("1234567", "usuario@teste.com")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("u***@teste.com", response.data["detail"])

        mock_gerar_token.assert_called_once_with(
            "1234567", "usuario@teste.com"
        )
        mock_enviar.assert_called_once()

    def test_post_username_length_boundaries(self):
        """Verifica o comportamento do endpoint com usernames nos limites válidos."""
        User.objects.create_user(
            username="7654321", email="teste7@teste.com", name="Teste 7"
        )

        response = self.client.post(
            self.url, {"username": "7654321"}, format="json"
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        User.objects.create_user(
            username="12345678", email="teste8@teste.com", name="Teste 8"
        )

        response = self.client.post(
            self.url, {"username": "12345678"}, format="json"
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_error_message_content(self):
        """Verifica se a mensagem de erro personalizada está correta"""
        view = EsqueciMinhaSenhaViewSet()

        expected_message = (
            "E-mail não encontrado! <br/>"
            "Para resolver este problema, entre em contato com o administrador do sistema."
        )

        self.assertEqual(view.MENSAGEM_EMAIL_NAO_CADASTRADO, expected_message)

    def test_post_username_exact_min_length(self):
        """Testa username com exatamente 7 caracteres"""
        User.objects.create_user(
            username="0000000", email="teste@teste.com", name="Teste Zero"
        )

        response = self.client.post(
            self.url, {"username": "0000000"}, format="json"
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_post_username_exact_max_length(self):
        """Testa username com exatamente 8 caracteres"""
        User.objects.create_user(
            username="99999999", email="teste@teste.com", name="Teste Nove"
        )

        response = self.client.post(
            self.url, {"username": "99999999"}, format="json"
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    @patch(
        "apps.usuarios.api.views.senha_view.SmeIntegracaoService.informacao_usuario_sgp"
    )
    def test_post_sme_exception_when_user_not_local(
        self, mock_informacao_usuario
    ):
        """Testa Exception na consulta SME quando usuário não existe localmente (linha 50-52)"""
        # Remove user from local DB
        User.objects.filter(username="8888888").delete()

        # SME raises exception
        mock_informacao_usuario.side_effect = Exception("SME Connection Error")

        response = self.client.post(
            self.url, {"username": "8888888"}, format="json"
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data["detail"], "Usuário não encontrado")

    @patch(
        "apps.usuarios.api.views.senha_view.SmeIntegracaoService.informacao_usuario_sgp"
    )
    @patch(
        "apps.usuarios.api.views.senha_view.SenhaService.gerar_token_para_reset"
    )
    @patch("apps.usuarios.api.views.senha_view.EnviaEmailService.enviar")
    @patch("apps.usuarios.api.views.senha_view.env")
    def test_post_email_from_second_api_call(
        self, mock_env, mock_enviar, mock_gerar_token, mock_informacao_usuario
    ):
        """Testa quando email vem da segunda chamada à API"""
        User.objects.create_user(
            username="5555555", email="", name="Usuário Sem Email Local"
        )

        mock_env.return_value = "http://localhost:8000"

        mock_informacao_usuario.return_value = {
            "email": "email_da_api@teste.com"
        }

        mock_gerar_token.return_value = {
            "uid": "test-uid",
            "token": "test-token",
            "name": "Usuário",
        }

        response = self.client.post(
            self.url, {"username": "5555555"}, format="json"
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("Enviamos um link", response.data["detail"])

        mock_gerar_token.assert_called_once_with(
            "5555555", "email_da_api@teste.com"
        )

    @patch(
        "apps.usuarios.api.views.senha_view.SmeIntegracaoService.informacao_usuario_sgp"
    )
    @patch(
        "apps.usuarios.api.views.senha_view.SenhaService.gerar_token_para_reset"
    )
    @patch("apps.usuarios.api.views.senha_view.EnviaEmailService.enviar")
    @patch("apps.usuarios.api.views.senha_view.env")
    def test_post_creates_local_user_from_sme_data(
        self, mock_env, mock_enviar, mock_gerar_token, mock_informacao_usuario
    ):
        """Testa criação de usuário local quando não existe (linha 58)"""
        # Garante que usuário não existe localmente
        User.objects.filter(username="7777777").delete()

        mock_env.return_value = "http://localhost:8000"

        # SME retorna dados completos do usuário
        mock_informacao_usuario.return_value = {
            "email": "novo_usuario@teste.com",
            "nome": "Novo Usuário",
            "numeroDocumento": "12345678900",
        }

        mock_gerar_token.return_value = {
            "uid": "test-uid",
            "token": "test-token",
            "name": "Novo Usuário",
        }

        # Verifica que usuário não existe antes
        self.assertFalse(User.objects.filter(username="7777777").exists())

        response = self.client.post(
            self.url, {"username": "7777777"}, format="json"
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("Enviamos um link", response.data["detail"])

        # Verifica que usuário foi criado localmente
        self.assertTrue(User.objects.filter(username="7777777").exists())

        # Verifica os dados do usuário criado
        user = User.objects.get(username="7777777")
        self.assertEqual(user.email, "novo_usuario@teste.com")
        self.assertEqual(user.name, "Novo Usuário")
        self.assertEqual(user.cpf, "12345678900")

        # Verifica que o email foi enviado
        mock_enviar.assert_called_once()
        mock_gerar_token.assert_called_once_with(
            "7777777", "novo_usuario@teste.com"
        )

    @patch(
        "apps.usuarios.api.views.senha_view.SmeIntegracaoService.informacao_usuario_sgp"
    )
    @patch("apps.usuarios.api.views.senha_view.User.objects.update_or_create")
    @patch("apps.usuarios.api.views.senha_view.env")
    def test_post_integrity_error_creating_local_user(
        self, mock_env, mock_update_or_create, mock_informacao_usuario
    ):
        """
        Testa IntegrityError ao tentar sincronizar usuário local (ex: email duplicado).
        Deve retornar EmailNaoCadastradoError com mensagem amigável.
        """
        mock_env.return_value = "http://localhost:8000"

        # Simula retorno da SME com dados
        mock_informacao_usuario.return_value = {
            "email": "duplicado@teste.com",
            "nome": "Usuário Duplicado",
            "numeroDocumento": "12345678900",
        }

        # Simula IntegrityError no banco de dados ao tentar salvar
        mock_update_or_create.side_effect = IntegrityError(
            "Duplicate entry for key 'email'"
        )

        response = self.client.post(
            self.url, {"username": "8888888"}, format="json"  # Username novo
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        # Verifica se a mensagem de erro personalizada foi retornada
        self.assertIn(
            "Já existe um usuário com este e-mail", response.data["detail"]
        )

    def test_criar_ou_atualizar_usuario_local_sem_nome(self):
        """
        Testa o método privado _criar_ou_atualizar_usuario_local quando não há nome nos dados SME.
        """
        view = EsqueciMinhaSenhaViewSet()
        username = "user_sem_nome"

        # Cria usuário local para ser retornado
        user = User.objects.create_user(
            username=username, email="original@teste.com", name="Nome Original"
        )

        # Dados simulados da SME sem a chave "nome" ou com valor vazio
        dados_sme = {"email": "novo@teste.com", "nome": ""}

        # Chama o método privado diretamente
        result = view._criar_ou_atualizar_usuario_local(username, dados_sme)

        # Verifica se retornou o usuário existente sem alterações
        self.assertEqual(result.id, user.id)

        user.refresh_from_db()
        # O email NÃO deve ter sido atualizado para "novo@teste.com"
        self.assertEqual(user.email, "original@teste.com")

    def test_criar_ou_atualizar_usuario_local_success_direct(self):
        """
        Testa o método privado _criar_ou_atualizar_usuario_local com sucesso via chamada direta.
        """
        view = EsqueciMinhaSenhaViewSet()
        username = "novo_user_direct"
        dados_sme = {
            "nome": "Novo Nome",
            "email": "novo@teste.com",
            "numeroDocumento": "11122233344",
        }

        # Garante que o usuário não existe antes do teste
        User.objects.filter(username=username).delete()

        # Chama o método privado diretamente
        result = view._criar_ou_atualizar_usuario_local(username, dados_sme)

        # Verificações
        self.assertEqual(result.username, username)
        self.assertEqual(result.name, "Novo Nome")
        self.assertEqual(result.email, "novo@teste.com")
        self.assertTrue(User.objects.filter(username=username).exists())

    def test_criar_ou_atualizar_usuario_local_lines_154_155(self):
        """
        Teste focado nas linhas 154-155 (transaction.atomic e update_or_create).
        Executa o método diretamente e verifica o efeito colateral no banco.
        """
        view = EsqueciMinhaSenhaViewSet()
        username = "usuario_teste_transacao"
        dados_sme = {
            "nome": "Nome Teste Transação",
            "email": "transacao@teste.com",
            "numeroDocumento": "11122233344",
        }

        # Garante que o usuário não existe antes
        User.objects.filter(username=username).delete()

        # Executa o método que contém o bloco transaction.atomic
        user_criado = view._criar_ou_atualizar_usuario_local(
            username, dados_sme
        )

        # Verificações
        self.assertIsNotNone(user_criado)
        self.assertEqual(user_criado.username, username)

        # Se o usuário existe no banco, o update_or_create (linha 155) funcionou
        self.assertTrue(User.objects.filter(username=username).exists())

    @patch(
        "apps.usuarios.api.views.senha_view.SmeIntegracaoService.informacao_usuario_sgp"
    )
    def test_post_sme_integracao_exception_when_user_not_local(
        self, mock_informacao_usuario
    ):
        """
        Testa SmeIntegracaoError na consulta SME quando usuário não existe localmente.
        Isso deve acionar a linha 83: raise UserNotFoundError
        """
        # 1. Garante que o usuário NÃO existe localmente
        User.objects.filter(username="8888888").delete()

        # 2. Faz o mock lançar especificamente SmeIntegracaoError
        # Importante: A exception deve ser a mesma classe importada na view
        mock_informacao_usuario.side_effect = SmeIntegracaoError(
            "Erro de conexão com SME"
        )

        response = self.client.post(
            self.url, {"username": "8888888"}, format="json"
        )

        # 3. Verifica se retornou (UserNotFoundError)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data["detail"], "Usuário não encontrado")


class TestRedefinirSenhaViewSet:
    """Testa o fluxo de redefinição de senha.

    Verifica o endpoint de redefinição de senha, incluindo sucesso,
    erro SME e validação de dados inválidos.
    """

    @patch("apps.usuarios.api.views.senha_view.RedefinirSenhaSerializer")
    @patch(
        "apps.usuarios.api.views.senha_view.SmeIntegracaoService.redefine_senha"
    )
    def test_post_success(self, mock_sme, mock_serializer):
        """Verifica que redefinição de senha bem-sucedida retorna status 200."""

        factory = APIRequestFactory()
        mock_sme.return_value = None

        mock_serializer_instance = MagicMock()
        mock_serializer_instance.is_valid.return_value = True
        mock_serializer_instance.validated_data = {
            "user": MagicMock(username="teste"),
            "new_pass": "NovaSenha@123",
        }

        mock_serializer.return_value = mock_serializer_instance

        request = factory.post(
            "/redefinir-senha/",
            {
                "uid": "fake_uid",
                "token": "fake_token",
                "new_pass": "NovaSenha@123",
                "new_pass_confirm": "NovaSenha@123",
            },
            format="json",
        )

        response = RedefinirSenhaViewSet.as_view()(request)

        assert response.status_code == status.HTTP_200_OK
        assert response.data["status"] == "success"

    @patch(
        "apps.usuarios.api.views.senha_view.SmeIntegracaoService.redefine_senha"
    )
    def test_post_sme_error(self, mock_sme):
        """Testa erro na SME."""
        factory = APIRequestFactory()
        mock_sme.side_effect = SmeIntegracaoError("Erro SME")

        data = {
            "uid": "x",
            "token": "x",
            "new_pass": "x",
            "new_pass_confirm": "x",
        }

        with patch(
            "apps.usuarios.api.serializers.senha_serializer.RedefinirSenhaSerializer"
        ) as mock_serializer:
            mock_serializer_instance = MagicMock()
            mock_serializer_instance.is_valid.return_value = True
            mock_serializer_instance.validated_data = {
                "user": MagicMock(),
                "new_pass": "x",
            }
            mock_serializer.return_value = mock_serializer_instance

            request = factory.post("/redefinir-senha/", data)
            view = RedefinirSenhaViewSet.as_view()
            response = view(request)

            assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_post_invalid_data(self):
        """Testa dados inválidos."""
        factory = APIRequestFactory()

        with patch(
            "apps.usuarios.api.serializers.senha_serializer.RedefinirSenhaSerializer"
        ) as mock_serializer:
            mock_serializer_instance = MagicMock()
            mock_serializer_instance.is_valid.side_effect = Exception()
            mock_serializer_instance.errors = {"error": "detalhe"}
            mock_serializer.return_value = mock_serializer_instance

            request = factory.post("/redefinir-senha/", {})
            view = RedefinirSenhaViewSet.as_view()
            response = view(request)

            assert response.status_code == status.HTTP_400_BAD_REQUEST

    @patch(
        "apps.usuarios.api.views.senha_view.SmeIntegracaoService.redefine_senha"
    )
    def test_post_sme_integracao_exception_returns_400(
        self, mock_redefine, django_user_model
    ):
        """Verifica que exceções de integração SME retornam erro 400."""
        password = secrets.token_urlsafe(16)

        user = django_user_model.objects.create_user(
            username="usuario", password=password
        )

        mock_redefine.side_effect = SmeIntegracaoError("Erro SME")

        uid = urlsafe_base64_encode(force_bytes(user.pk))
        token = default_token_generator.make_token(user)

        data = {
            "uid": uid,
            "token": token,
            "new_pass": "NovaSenha@123",
            "new_pass_confirm": "NovaSenha@123",
        }

        request = APIRequestFactory().post("/reset/", data, format="json")
        response = RedefinirSenhaViewSet.as_view()(request)

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert response.data["status"] == "error"
        assert "Erro SME" in response.data["detail"]

    @patch(
        "apps.usuarios.api.views.senha_view.SmeIntegracaoService.redefine_senha"
    )
    @patch("django.contrib.auth.models.AbstractBaseUser.save")
    def test_post_password_updated_in_sme_but_local_save_fails(
        self, mock_save, mock_redefine, django_user_model
    ):
        """Deve retornar erro quando salvamento local falhar após redefinição no SME."""
        password = secrets.token_urlsafe(16)

        user = django_user_model.objects.create_user(
            username="usuario", password=password
        )

        mock_redefine.return_value = None
        mock_save.side_effect = Exception("DB error")

        uid = urlsafe_base64_encode(force_bytes(user.pk))
        token = default_token_generator.make_token(user)

        data = {
            "uid": uid,
            "token": token,
            "new_pass": "NovaSenha@123",
            "new_pass_confirm": "NovaSenha@123",
        }

        request = APIRequestFactory().post("/reset/", data, format="json")
        response = RedefinirSenhaViewSet.as_view()(request)

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert response.data["status"] == "error"

    @pytest.mark.django_db
    @patch(
        "apps.usuarios.api.views.senha_view.SmeIntegracaoService.redefine_senha"
    )
    def test_redefine_senha_view_success(
        self,
        mock_redefine_senha,
        client,
        django_user_model,
    ):
        """Deve redefinir senha com sucesso e atualizar usuário local."""
        password = secrets.token_urlsafe(16)

        user = django_user_model.objects.create_user(
            username="teste", password=password
        )

        uid = urlsafe_base64_encode(force_bytes(user.pk))
        token = default_token_generator.make_token(user)

        payload = {
            "uid": uid,
            "token": token,
            "new_pass": password,
            "new_pass_confirm": password,
        }

        mock_redefine_senha.return_value = "OK"

        response = client.post(
            "/api/usuario/redefinir-senha",
            payload,
            content_type="application/json",
        )

        assert response.status_code == 200

        mock_redefine_senha.assert_called_once_with(user.username, password)

        user.refresh_from_db()
        assert user.check_password(password)


@pytest.mark.django_db
class TestAtualizarSenhaViewSet:
    """Testa a view de atualização de senha do usuário autenticado."""

    password = secrets.token_urlsafe(16)
    old_password = secrets.token_urlsafe(16)

    def test_sucesso(self, view, mock_request):
        """Verifica atualização de senha com request válido."""

        mock_request.data = {
            "username": "testuser",
            "senha_atual": self.old_password,
            "nova_senha": self.password,
            "confirmacao_nova_senha": self.password,
        }

        mock_serializer = MagicMock()
        mock_serializer.is_valid.return_value = True
        mock_serializer.validated_data = {"nova_senha": self.password}

        with patch(
            "apps.usuarios.api.serializers.senha_serializer.AtualizarSenhaSerializer"
        ) as mock_serializer_class:
            mock_serializer_class.return_value = mock_serializer

            with patch(
                "apps.usuarios.services.sme_integracao_service.SmeIntegracaoService.redefine_senha"
            ):
                with patch.object(mock_request.user, "set_password"):
                    with patch.object(mock_request.user, "save"):
                        response = view.post(mock_request)

        assert response.status_code == status.HTTP_200_OK
        assert response.data["detail"] == "Senha alterada com sucesso."

    def test_validation_error_confirmacao_senha_nao_corresponde(
        self, view, mock_request
    ):
        """Verifica erro quando a confirmação de senha não coincide."""
        mock_request.data = {
            "username": "testuser",
            "senha_atual": self.old_password,
            "nova_senha": self.password,
            "confirmacao_nova_senha": f"{self.password}_diferente",
        }

        mock_serializer = MagicMock()
        mock_serializer.is_valid.return_value = False
        mock_serializer.errors = {
            "confirmacao_nova_senha": ["As senhas não coincidem."]
        }

        with patch(
            "apps.usuarios.api.serializers.senha_serializer.AtualizarSenhaSerializer"
        ) as mock_serializer_class:
            mock_serializer_class.return_value = mock_serializer

            response = view.post(mock_request)

        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_validation_error_senha_atual_incorreta_pela_view(
        self, view, mock_request
    ):
        """Verifica erro quando a senha atual informada está incorreta."""
        mock_request.data = {
            "username": "testuser",
            "senha_atual": "senha_errada",
            "nova_senha": self.password,
            "confirmacao_nova_senha": self.password,
        }

        mock_request.user.check_password.return_value = False

        response = view.post(mock_request)

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert response.data["detail"] == "Senha atual incorreta."
        assert response.data["field"] == "senha_atual"

    def test_serializer_raise_exception_true_line(self, mock_request):
        """Verifica validação de serializer com raise_exception=True."""
        data = {
            "username": "",
            "senha_atual": "",
            "nova_senha": "",
            "confirmacao_nova_senha": "",
        }

        serializer = AtualizarSenhaSerializer(
            data=data, context={"request": mock_request}
        )

        with pytest.raises(serializers.ValidationError) as exc_info:
            serializer.is_valid(raise_exception=True)

        detail = exc_info.value.detail
        assert "detail" in detail
        assert "field" in detail

    def test_erro_sme(self, view, mock_request):
        """Verifica retorno 400 quando SME lança erro durante atualização de senha."""
        mock_request.data = {
            "username": "testuser",
            "senha_atual": self.old_password,
            "nova_senha": self.password,
            "confirmacao_nova_senha": self.password,
        }

        mock_serializer = MagicMock()
        mock_serializer.is_valid.return_value = True
        mock_serializer.validated_data = {"nova_senha": self.password}

        with patch(
            "apps.usuarios.api.serializers.senha_serializer.AtualizarSenhaSerializer"
        ) as mock_serializer_class:
            mock_serializer_class.return_value = mock_serializer

            with patch(
                "apps.usuarios.services.sme_integracao_service.SmeIntegracaoService.redefine_senha",
                side_effect=SmeIntegracaoError("Erro SME"),
            ):
                response = view.post(mock_request)

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "Erro SME" in response.data["detail"]

    def test_erro_inesperado(self, view, mock_request):
        """Verifica retorno 500 em caso de exceção genérica inesperada."""
        mock_request.data = {
            "username": "testuser",
            "senha_atual": self.old_password,
            "nova_senha": self.password,
            "confirmacao_nova_senha": self.password,
        }

        mock_serializer = MagicMock()
        mock_serializer.is_valid.return_value = True
        mock_serializer.validated_data = {"nova_senha": self.password}

        with patch(
            "apps.usuarios.api.serializers.senha_serializer.AtualizarSenhaSerializer"
        ) as mock_serializer_class:
            mock_serializer_class.return_value = mock_serializer

            with patch(
                "apps.usuarios.services.sme_integracao_service.SmeIntegracaoService.redefine_senha",
                side_effect=Exception("Erro inesperado"),
            ):
                with patch(
                    "apps.usuarios.api.views.senha_view.logger.exception"
                ):
                    response = view.post(mock_request)

        assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
        assert response.data["detail"] == "Erro interno do servidor."
