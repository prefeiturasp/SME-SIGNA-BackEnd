import pytest
from django.urls import reverse
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient
from rest_framework_simplejwt.tokens import AccessToken

User = get_user_model()

@pytest.fixture
def api_client():
    return APIClient()

@pytest.fixture
def user(db):
    # Cria um usuário simples de teste
    return User.objects.create_user(
        username="vinicius",
        email="vinicius@example.com",
        password="pass1234",
        is_staff=False,
        is_superuser=False,
    )

# ---------- profile (protegida) ----------

@pytest.mark.django_db
def test_profile_unauthenticated_returns_401(api_client):
    url = reverse("api-profile")
    resp = api_client.get(url)
    assert resp.status_code == 401
    # DRF SimpleJWT normalmente retorna detail
    assert "detail" in resp.data

@pytest.mark.django_db
def test_profile_authenticated_returns_user_data(api_client, user):
    url = reverse("api-profile")
    # Autentica via session ou DRF force_authenticate
    api_client.force_authenticate(user=user)
    resp = api_client.get(url)
    assert resp.status_code == 200
    assert resp.data["id"] == user.id
    assert resp.data["username"] == user.username
    assert resp.data["email"] == user.email
    assert resp.data["is_staff"] == user.is_staff
    assert resp.data["is_superuser"] == user.is_superuser

# ---------- debug_headers (pública) ----------

@pytest.mark.django_db
def test_debug_headers_includes_auth_headers_when_present(api_client):
    url = reverse("debug-headers")
    resp = api_client.get(url, HTTP_AUTHORIZATION="Bearer dummy-token")
    # Aceita 200 ou 401 conforme a configuração global
    assert resp.status_code in (200, 401)
    if resp.status_code == 200:
        assert "HTTP_AUTHORIZATION" in resp.data
        assert resp.data["HTTP_AUTHORIZATION"] == "Bearer dummy-token"

@pytest.mark.django_db
def test_debug_headers_without_auth_header(api_client):
    url = reverse("debug-headers")
    resp = api_client.get(url)
    assert resp.status_code == 200
    # Sem header AUTH, pode retornar dict vazio ou sem a chave específica
    assert "HTTP_AUTHORIZATION" not in resp.data

# ---------- debug_authenticate (pública, mas tenta autenticar via JWT) ----------

@pytest.mark.django_db
def test_debug_authenticate_without_token_returns_none(api_client):
    url = reverse("debug-auth")
    resp = api_client.get(url)
    assert resp.status_code == 200
    # A view retorna {"authenticate": None, "detail": "..."} quando não há token
    assert resp.data.get("authenticate") is None

@pytest.mark.django_db
def test_debug_authenticate_with_valid_jwt(api_client, user, settings):
    url = reverse("debug-auth")

    # Gera um JWT válido para o usuário
    access = AccessToken.for_user(user)
    token = str(access)

    # Chama com Authorization: Bearer <token>
    resp = api_client.get(url, HTTP_AUTHORIZATION=f"Bearer {token}")
    assert resp.status_code == 200
    assert resp.data.get("authenticate") == "ok"
    assert resp.data.get("username") == user.username
    assert resp.data.get("user_id") == user.id

    # O payload deve conter pelo menos sub/exp/jti ou claims do SimpleJWT
    token_payload = resp.data.get("token_payload")
    assert isinstance(token_payload, dict)
    # Verificações básicas (chaves variam por versão/config)
    assert "token_type" in token_payload or "typ" in token_payload
    assert "exp" in token_payload