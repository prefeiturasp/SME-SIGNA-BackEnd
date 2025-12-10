import pytest
from unittest.mock import patch
from django.contrib.auth import get_user_model
from apps.usuarios.services.sme_integracao_service import SmeIntegracaoService
from apps.helpers.exceptions import AuthenticationError

User = get_user_model()

SME_POST_PATH = "apps.usuarios.services.sme_integracao_service.requests.post"


@pytest.fixture
def mock_sme_success():
    """Mocka resposta de sucesso do CoreSSO"""
    with patch(SME_POST_PATH) as mock:
        mock.return_value.status_code = 200
        mock.return_value.json.return_value = {
            "nome": "João da Silva",
            "email": "joao@email.com",
            "numeroDocumento": "12345678900",
        }
        yield mock


@pytest.fixture
def mock_sme_unauthorized():
    """Mocka retorno 401"""
    with patch(SME_POST_PATH) as mock:
        mock.return_value.status_code = 401
        yield mock


@pytest.fixture
def mock_sme_error():
    """Mocka retorno != 200 e != 401"""
    with patch(SME_POST_PATH) as mock:
        mock.return_value.status_code = 500
        yield mock


@pytest.fixture
def mock_sme_exception():
    """Mocka erro de comunicação (timeout, conexão etc.)"""
    with patch(SME_POST_PATH, side_effect=Exception("Erro")):
        yield


@pytest.fixture
def mock_sme_auth_error(monkeypatch):
    def fake_autentica(login, senha):
        raise AuthenticationError()

    monkeypatch.setattr(SmeIntegracaoService, "autentica", fake_autentica)
