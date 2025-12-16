import pytest
from apps.usuarios.services.sme_integracao_service import SmeIntegracaoService
from apps.helpers.exceptions import (
    AuthenticationError,
    SmeIntegracaoException,
    InternalError
)
import requests
from unittest.mock import patch, MagicMock


class FakeResponse:
    def __init__(self, status, data=None):
        self.status_code = status
        self._data = data or {}

    def json(self):
        return self._data


def test_sme_autentica_success(monkeypatch):
    def fake_post(*args, **kwargs):
        return FakeResponse(
            200,
            {"nome": "João", "email": "joao@email.com"}
        )

    monkeypatch.setattr(requests, "post", fake_post)

    result = SmeIntegracaoService.autentica("1234", "senha")

    assert result["nome"] == "João"


def test_sme_autentica_unauthorized(monkeypatch):
    def fake_post(*args, **kwargs):
        return FakeResponse(401)

    monkeypatch.setattr(requests, "post", fake_post)

    with pytest.raises(AuthenticationError):
        SmeIntegracaoService.autentica("1234", "errada")


def test_sme_autentica_other_status(monkeypatch):
    def fake_post(*args, **kwargs):
        return FakeResponse(500)

    monkeypatch.setattr(requests, "post", fake_post)

    with pytest.raises(SmeIntegracaoException):
        SmeIntegracaoService.autentica("1234", "senha")


def test_sme_autentica_request_exception(monkeypatch):
    def fake_post(*args, **kwargs):
        raise requests.exceptions.RequestException("timeout")

    monkeypatch.setattr(requests, "post", fake_post)

    with pytest.raises(SmeIntegracaoException):
        SmeIntegracaoService.autentica("1234", "senha")


def test_sme_autentica_internal_error(monkeypatch):
    def fake_post(*args, **kwargs):
        raise ValueError("erro inesperado")

    monkeypatch.setattr(requests, "post", fake_post)

    with pytest.raises(InternalError):
        SmeIntegracaoService.autentica("1234", "senha")


def test_informacao_usuario_sgp_success():
    """Testa quando a API retorna 200 com dados"""
    with patch('requests.get') as mock_get:
        mock_response = MagicMock(status_code=200)
        mock_response.json.return_value = {"email": "teste@email.com"}
        mock_get.return_value = mock_response
        
        result = SmeIntegracaoService.informacao_usuario_sgp("1234567")
        
        assert result == {"email": "teste@email.com"}
        mock_get.assert_called_once()


def test_informacao_usuario_sgp_not_found():
    """Testa quando a API retorna 404"""
    with patch('requests.get') as mock_get:
        mock_response = MagicMock(status_code=404)
        mock_get.return_value = mock_response
        
        with pytest.raises(SmeIntegracaoException) as exc:
            SmeIntegracaoService.informacao_usuario_sgp("1234567")
        
        assert "Dados não encontrados" in str(exc.value)


def test_informacao_usuario_sgp_other_error_status():
    """Testa quando a API retorna outro erro (ex: 500)"""
    with patch('requests.get') as mock_get:
        mock_response = MagicMock(status_code=500)
        mock_get.return_value = mock_response
        
        with pytest.raises(SmeIntegracaoException) as exc:
            SmeIntegracaoService.informacao_usuario_sgp("1234567")


def test_informacao_usuario_sgp_connection_error():
    """Testa quando há erro de conexão"""
    with patch('requests.get') as mock_get:
        mock_get.side_effect = requests.exceptions.ConnectionError
        
        with pytest.raises(requests.exceptions.RequestException):
            SmeIntegracaoService.informacao_usuario_sgp("1234567")
