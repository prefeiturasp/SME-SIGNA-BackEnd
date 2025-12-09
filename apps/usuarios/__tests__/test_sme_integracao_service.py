import pytest
from apps.usuarios.services.sme_integracao_service import SmeIntegracaoService
from apps.helpers.exceptions import (
    AuthenticationError,
    SmeIntegracaoException,
    InternalError
)
import requests


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
