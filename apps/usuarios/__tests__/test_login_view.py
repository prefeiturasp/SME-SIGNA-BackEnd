import pytest
import secrets
from unittest.mock import patch
from django.urls import reverse
from django.contrib.auth import get_user_model
from unittest.mock import patch
from rest_framework.test import APIClient
from apps.helpers.exceptions import (
    SmeIntegracaoException
)

User = get_user_model()

@pytest.fixture(autouse=True)
def set_signa_env(monkeypatch):
    monkeypatch.setenv("CODIGO_SISTEMA_SIGNA", "0000")


@pytest.mark.django_db
def test_login_success(client, mock_sme_success):
    url = reverse("login")
    password = secrets.token_urlsafe(16)

    payload = {
        "username": "1234567",
        "password": password,
    }

    response = client.post(url, payload)

    assert response.status_code == 200
    data = response.json()

    assert "token" in data
    assert data["name"] == "João da Silva"
    assert data["email"] == "joao@email.com"

    user = User.objects.filter(username="1234567").first()
    assert user is not None
    assert user.name == "João da Silva"
    assert user.check_password(password)



@pytest.mark.django_db
def test_login_unauthorized(client, mock_sme_unauthorized):
    url = reverse("login")

    payload = {
        "username": "0000000",
        "password": secrets.token_urlsafe(16),
    }

    response = client.post(url, payload)

    assert response.status_code == 401
    assert response.json()["detail"] == "Usuário ou senha inválidos"


@pytest.mark.django_db
def test_login_sme_error(client, mock_sme_error):
    url = reverse("login")

    payload = {
        "username": "0000",
        "password": secrets.token_urlsafe(16),
    }

    response = client.post(url, payload)

    assert response.status_code == 400
    assert "Credenciais inválidas" in response.json()["detail"]


@pytest.mark.django_db
def test_login_sme_exception(client, mock_sme_exception):
    url = reverse("login")

    payload = {
        "username": "0000",
        "password": secrets.token_urlsafe(16),
    }

    response = client.post(url, payload)

    assert response.status_code == 400
    assert "Credenciais inválidas" in response.json()["detail"]


@pytest.mark.django_db
def test_login_updates_existing_user(client, mock_sme_success):
    old_password = secrets.token_urlsafe(16)

    user = User.objects.create_user(
        username="1234567",
        password=old_password,
        name="Antigo",
        email="old@mail.com"
    )

    new_password = secrets.token_urlsafe(16)

    url = reverse("login")
    payload = {
        "username": "1234567",
        "password": new_password,
    }

    response = client.post(url, payload)

    assert response.status_code == 200

    user.refresh_from_db()

    assert user.name == "João da Silva"
    assert user.email == "joao@email.com"
    assert user.check_password(new_password)


@pytest.mark.django_db
def test_login_authentication_error(client, mock_sme_auth_error):
    wrong_password = secrets.token_urlsafe(16)
    url = reverse("login")
    payload = {"username": "1234567", "password": wrong_password}

    response = client.post(url, payload)

    assert response.status_code == 401
    assert response.json()["detail"] == "Usuário ou senha inválidos"


@pytest.mark.django_db
def test_login_sme_integracao_exception():
    wrong_password = secrets.token_urlsafe(16)
    client = APIClient()
    url = reverse("login")

    with patch("apps.usuarios.services.sme_integracao_service.SmeIntegracaoService.autentica") as mocked_login:
        mocked_login.side_effect = SmeIntegracaoException("Falha SME")

        response = client.post(url, {"username": "12345678", "password": wrong_password}, format="json")

    assert response.status_code == 400
    assert response.json()["detail"] == (
        "Parece que estamos com uma instabilidade no momento. Tente entrar novamente daqui a pouco."
    )

@pytest.mark.django_db
def test_login_generic_exception():
    password = secrets.token_urlsafe(16)
    client = APIClient()
    url = reverse("login")

    with patch("apps.usuarios.services.sme_integracao_service.SmeIntegracaoService.autentica") as mocked_login:
        mocked_login.side_effect = Exception("Erro inesperado")

        response = client.post(url, {"username": "1234567", "password": password}, format="json")

    assert response.status_code == 500
    assert response.json()["detail"] == "Erro interno"


@pytest.mark.django_db
def test_login_perfil_nao_autorizado_sem_perfis(client, monkeypatch):
    url = reverse("login")
    password = "senha123"

    monkeypatch.setenv("CODIGO_SISTEMA_SIGNA", "0000")

    with patch(
        "apps.usuarios.services.sme_integracao_service.SmeIntegracaoService.autentica"
    ) as mocked:
        mocked.return_value = {
            "nome": "João",
            "email": "joao@email.com",
            "numeroDocumento": "12345678900",
        }

        response = client.post(
            url,
            {"username": "1234567", "password": password},
            format="json",
        )

    assert response.status_code == 401
    assert response.json()["detail"] == (
        "Desculpe, mas o acesso ao SIGNA é restrito a perfis específicos."
    )


@pytest.mark.django_db
def test_login_perfil_nao_autorizado_perfis_nao_lista(client, monkeypatch):
    url = reverse("login")
    password = "senha123"

    monkeypatch.setenv("CODIGO_SISTEMA_SIGNA", "0000")

    with patch(
        "apps.usuarios.services.sme_integracao_service.SmeIntegracaoService.autentica"
    ) as mocked:
        mocked.return_value = {
            "nome": "João",
            "email": "joao@email.com",
            "numeroDocumento": "12345678900",
            "perfis": "0000",
        }

        response = client.post(
            url,
            {"username": "1234567", "password": password},
            format="json",
        )

    assert response.status_code == 401
    assert response.json()["detail"] == (
        "Desculpe, mas o acesso ao SIGNA é restrito a perfis específicos."
    )


@pytest.mark.django_db
def test_login_perfil_nao_autorizado_codigo_signa_nao_presente(client, monkeypatch):
    url = reverse("login")
    password = "senha123"

    monkeypatch.setenv("CODIGO_SISTEMA_SIGNA", "SIGNACODE")

    with patch(
        "apps.usuarios.services.sme_integracao_service.SmeIntegracaoService.autentica"
    ) as mocked:
        mocked.return_value = {
            "nome": "João",
            "email": "joao@email.com",
            "numeroDocumento": "12345678900",
            "perfis": [
                "OUTRO-SISTEMA",
                "SISTEMA-TESTE",
            ], 
        }

        response = client.post(
            url,
            {"username": "1234567", "password": password},
            format="json",
        )

    assert response.status_code == 401
    assert response.json()["detail"] == (
        "Desculpe, mas o acesso ao SIGNA é restrito a perfis específicos."
    )
