import pytest
import os
import secrets
from unittest.mock import patch, MagicMock
from django.test import TestCase
from rest_framework.test import APIRequestFactory
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient
from rest_framework import status

from django.contrib.auth import get_user_model
from django.contrib.auth.tokens import default_token_generator
from django.test import override_settings
from django.utils.encoding import force_bytes
from django.utils.http import urlsafe_base64_encode

from apps.usuarios.api.views.senha_view import EsqueciMinhaSenhaViewSet, RedefinirSenhaViewSet
from apps.helpers.exceptions import SmeIntegracaoException

User = get_user_model()

class TestEsqueciMinhaSenhaViewSet(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        os.environ["AMBIENTE_URL"] = "http://testserver"

    def setUp(self):
        self.client = APIClient()
        self.url = "/api/usuario/esqueci-senha"
        
        User.objects.all().delete()
        
        self.user = User.objects.create_user(
            username="1234567",
            email="usuario@teste.com",
            name="Usuário Teste"
        )
        
        self.valid_data = {"username": "1234567"}
    
    def tearDown(self):
        User.objects.all().delete()
    
    @patch("apps.usuarios.api.views.senha_view.SmeIntegracaoService.informacao_usuario_sgp")
    @patch("apps.usuarios.api.views.senha_view.SenhaService.gerar_token_para_reset")
    @patch("apps.usuarios.api.views.senha_view.EnviaEmailService.enviar")
    @patch("apps.usuarios.api.views.senha_view.env")
    def test_post_success_local_user_with_email(
        self, mock_env, mock_enviar, mock_gerar_token, mock_informacao_usuario
    ):
        """Testa fluxo normal onde usuário existe localmente e tem email"""
        mock_env.return_value = "http://localhost:8000"
        mock_informacao_usuario.return_value = {"email": "usuario@teste.com"}
        mock_gerar_token.return_value = {
            "uid": "test-uid",
            "token": "test-token",
            "name": "Usuário"
        }
        response = self.client.post(self.url, self.valid_data, format="json")
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("Enviamos um link", response.data["detail"])
        
        mock_gerar_token.assert_called_once_with("1234567", "usuario@teste.com")
        mock_enviar.assert_called_once()

    @patch("apps.usuarios.api.views.senha_view.SmeIntegracaoService.informacao_usuario_sgp")
    @patch("apps.usuarios.api.views.senha_view.SenhaService.gerar_token_para_reset")
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
            "name": "Usuário"
        }
        response = self.client.post(self.url, self.valid_data, format="json")
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("Enviamos um link", response.data["detail"])
        self.assertIn("u*@teste.com", response.data["detail"])
        
        mock_gerar_token.assert_called_once_with("1234567", "us@teste.com")
        mock_enviar.assert_called_once()


    @patch("apps.usuarios.api.views.senha_view.SmeIntegracaoService.informacao_usuario_sgp")
    @patch("apps.usuarios.api.views.senha_view.SenhaService.gerar_token_para_reset")
    @patch("apps.usuarios.api.views.senha_view.EnviaEmailService.enviar")
    @patch("apps.usuarios.api.views.senha_view.env")
    def test_post_success_api_email(
        self, mock_env, mock_enviar, mock_gerar_token, mock_informacao_usuario
    ):
        """Testa fluxo onde usuário existe localmente mas email vem da API"""
        user = User.objects.create_user(
            username="7654321",
            email="",
            name="Usuário Sem Email"
        )
        
        mock_env.return_value = "http://localhost:8000"
        mock_informacao_usuario.return_value = {"email": "novo@api.com"}
        mock_gerar_token.return_value = {
            "uid": "test-uid",
            "token": "test-token",
            "name": "Usuário"
        }
        
        response = self.client.post(self.url, {"username": "7654321"}, format="json")
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        mock_informacao_usuario.assert_called_once_with("7654321")
    
    def test_post_user_not_found(self):
        """Testa quando usuário não existe no banco local"""
        response = self.client.post(
            self.url, 
            {"username": "9999999"}, 
            format="json"
        )
        
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertEqual(response.data["detail"], "Usuário não encontrado")
    
    @patch("apps.usuarios.api.views.senha_view.SmeIntegracaoService.informacao_usuario_sgp")
    def test_post_email_not_found_anywhere(
        self, mock_informacao_usuario
    ):
        """Testa quando email não é encontrado nem na API nem localmente"""
        user = User.objects.create_user(
            username="1111111",
            email="",
            name="Usuário Sem Email"
        )
        
        mock_informacao_usuario.return_value = {}
        
        response = self.client.post(
            self.url, 
            {"username": "1111111"},
            format="json"
        )
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("E-mail não encontrado!", response.data["detail"])
    
    def test_post_invalid_data(self):
        """Testa com dados inválidos (username muito curto)"""
        invalid_data = {"username": "123"}
        
        response = self.client.post(self.url, invalid_data, format="json")
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("username", response.data)
    
    @patch("apps.usuarios.api.views.senha_view.SmeIntegracaoService.informacao_usuario_sgp")
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
        
        self.assertEqual(response.status_code, status.HTTP_500_INTERNAL_SERVER_ERROR)
        self.assertEqual(response.data["detail"], "Erro interno no servidor.")
    
    @patch("apps.usuarios.api.views.senha_view.SenhaService.gerar_token_para_reset")
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
            "name": "Usuário"
        }
        mock_anonimizar.return_value = "u***@teste.com"
        
        view = EsqueciMinhaSenhaViewSet()
        
        response = view._processar_envio_email("1234567", "usuario@teste.com")
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("u***@teste.com", response.data["detail"])
        
        mock_gerar_token.assert_called_once_with("1234567", "usuario@teste.com")
        mock_enviar.assert_called_once()
    
    def test_post_username_length_boundaries(self):
        """Testa username com 7 e 8 caracteres (limites do serializer)"""
        user_7 = User.objects.create_user(
            username="7654321",
            email="teste7@teste.com",
            name="Teste 7"
        )
        
        response = self.client.post(
            self.url, 
            {"username": "7654321"},
            format="json"
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        user_8 = User.objects.create_user(
            username="12345678",
            email="teste8@teste.com",
            name="Teste 8"
        )
        
        response = self.client.post(
            self.url, 
            {"username": "12345678"},
            format="json"
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
        user = User.objects.create_user(
            username="0000000", 
            email="teste@teste.com",
            name="Teste Zero"
        )
        
        response = self.client.post(
            self.url,
            {"username": "0000000"},
            format="json"
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
    
    def test_post_username_exact_max_length(self):
        """Testa username com exatamente 8 caracteres"""
        user = User.objects.create_user(
            username="99999999",
            email="teste@teste.com",
            name="Teste Nove"
        )
        
        response = self.client.post(
            self.url,
            {"username": "99999999"},
            format="json"
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)


class TestRedefinirSenhaViewSet:
    
    @patch("apps.usuarios.api.views.senha_view.RedefinirSenhaSerializer")
    @patch("apps.usuarios.api.views.senha_view.SmeIntegracaoService.redefine_senha")
    def test_post_success(self, mock_sme, mock_serializer):
        """Testa sucesso total."""

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
    
    @patch('apps.usuarios.api.views.senha_view.SmeIntegracaoService.redefine_senha')
    def test_post_sme_error(self, mock_sme):
        """Testa erro na SME."""
        factory = APIRequestFactory()
        mock_sme.side_effect = SmeIntegracaoException("Erro SME")
        
        data = {"uid": "x", "token": "x", "new_pass": "x", "new_pass_confirm": "x"}
        
        with patch('apps.usuarios.api.serializers.senha_serializer.RedefinirSenhaSerializer') as mock_serializer:
            mock_serializer_instance = MagicMock()
            mock_serializer_instance.is_valid.return_value = True
            mock_serializer_instance.validated_data = {"user": MagicMock(), "new_pass": "x"}
            mock_serializer.return_value = mock_serializer_instance
            
            request = factory.post('/redefinir-senha/', data)
            view = RedefinirSenhaViewSet.as_view()
            response = view(request)
            
            assert response.status_code == status.HTTP_400_BAD_REQUEST
    
    def test_post_invalid_data(self):
        """Testa dados inválidos."""
        factory = APIRequestFactory()
        
        with patch('apps.usuarios.api.serializers.senha_serializer.RedefinirSenhaSerializer') as mock_serializer:
            mock_serializer_instance = MagicMock()
            mock_serializer_instance.is_valid.side_effect = Exception()
            mock_serializer_instance.errors = {"error": "detalhe"}
            mock_serializer.return_value = mock_serializer_instance
            
            request = factory.post('/redefinir-senha/', {})
            view = RedefinirSenhaViewSet.as_view()
            response = view(request)
            
            assert response.status_code == status.HTTP_400_BAD_REQUEST

    @patch("apps.usuarios.api.views.senha_view.SmeIntegracaoService.redefine_senha")
    def test_post_sme_integracao_exception_returns_400(self, mock_redefine, django_user_model):
        password = secrets.token_urlsafe(16)

        user = django_user_model.objects.create_user(
            username="usuario",
            password=password
        )

        mock_redefine.side_effect = SmeIntegracaoException("Erro SME")

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

    @patch("apps.usuarios.api.views.senha_view.SmeIntegracaoService.redefine_senha")
    @patch("django.contrib.auth.models.AbstractBaseUser.save")
    def test_post_password_updated_in_sme_but_local_save_fails(
        self, mock_save, mock_redefine, django_user_model
    ):
        password = secrets.token_urlsafe(16)
    
        user = django_user_model.objects.create_user(
            username="usuario",
            password=password
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
    def test_redefine_senha_view_success(self, client, django_user_model):
        password = secrets.token_urlsafe(16)
        user = django_user_model.objects.create_user(
            username="teste",
            password=password
        )

        uid = urlsafe_base64_encode(force_bytes(user.pk))
        token = default_token_generator.make_token(user)

        payload = {
            "uid": uid,
            "token": token,
            "new_pass": password,
            "new_pass_confirm": password
        }

        response = client.post(
            f"/api/usuario/redefinir-senha",
            payload,
            content_type="application/json"
        )

        user.refresh_from_db()

        assert response.status_code == 200
        assert user.check_password(password)

