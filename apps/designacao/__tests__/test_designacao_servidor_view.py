import pytest
from unittest.mock import patch, MagicMock

from django.contrib.auth import get_user_model
from rest_framework.test import APIClient
from rest_framework import status
from rest_framework.exceptions import ValidationError

from apps.helpers.exceptions import SmeIntegracaoException

User = get_user_model()

@pytest.fixture
def client():
    return APIClient()


@pytest.fixture
def user(db):
    return User.objects.create_user(
        username="usuario",
        password="senha123"
    )


@pytest.fixture
def auth_client(client, user):
    client.force_authenticate(user=user)
    return client


@pytest.fixture
def url():
    return "/api/designacao/servidor"


@patch(
    "apps.designacao.api.views.designacao_servidor_view."
    "DesignacaoServidorRequestSerializer"
)
def test_post_serializer_invalido(
    mock_serializer,
    auth_client,
    url
):
    serializer_instance = MagicMock()
    serializer_instance.is_valid.side_effect = ValidationError("erro")
    mock_serializer.return_value = serializer_instance

    response = auth_client.post(
        url,
        {"rf": ""},
        format="json"
    )

    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert response.data["detail"] == "RF inválido"

@patch(
    "apps.designacao.api.views.designacao_servidor_view."
    "DesignacaoServidorService.obter_designacao"
)
@patch(
    "apps.designacao.api.views.designacao_servidor_view."
    "DesignacaoServidorRequestSerializer"
)
def test_post_sucesso(
    mock_serializer,
    mock_service,
    auth_client,
    url
):
    serializer_instance = MagicMock()
    serializer_instance.is_valid.return_value = True
    serializer_instance.validated_data = {"rf": "0000000"}
    mock_serializer.return_value = serializer_instance

    mock_service.return_value = {
        "nome": "João",
        "rf": "0000000"
    }

    response = auth_client.post(
        url,
        {"rf": "0000000"},
        format="json"
    )

    assert response.status_code == status.HTTP_200_OK
    assert response.data["nome"] == "João"
    assert response.data["rf"] == "0000000"

    mock_service.assert_called_once_with("0000000")

@patch(
    "apps.designacao.api.views.designacao_servidor_view."
    "DesignacaoServidorService.obter_designacao"
)
@patch(
    "apps.designacao.api.views.designacao_servidor_view."
    "DesignacaoServidorRequestSerializer"
)
def test_post_sme_integracao_exception(
    mock_serializer,
    mock_service,
    auth_client,
    url
):
    serializer_instance = MagicMock()
    serializer_instance.is_valid.return_value = True
    serializer_instance.validated_data = {"rf": "0000000"}
    mock_serializer.return_value = serializer_instance

    mock_service.side_effect = SmeIntegracaoException(
        "Erro SME"
    )

    response = auth_client.post(
        url,
        {"rf": "0000000"},
        format="json"
    )

    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert response.data["detail"] == "Erro SME"

@patch(
    "apps.designacao.api.views.designacao_servidor_view."
    "DesignacaoServidorService.obter_designacao"
)
@patch(
    "apps.designacao.api.views.designacao_servidor_view."
    "DesignacaoServidorRequestSerializer"
)
def test_post_exception_generica(
    mock_serializer,
    mock_service,
    auth_client,
    url
):
    serializer_instance = MagicMock()
    serializer_instance.is_valid.return_value = True
    serializer_instance.validated_data = {"rf": "0000000"}
    mock_serializer.return_value = serializer_instance

    mock_service.side_effect = Exception(
        "Erro inesperado"
    )

    response = auth_client.post(
        url,
        {"rf": "0000000"},
        format="json"
    )

    assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
    assert response.data["detail"] == "Erro interno"

def test_post_sem_autenticacao(client, url):
    response = client.post(
        url,
        {"rf": "0000000"},
        format="json"
    )

    assert response.status_code == status.HTTP_401_UNAUTHORIZED
