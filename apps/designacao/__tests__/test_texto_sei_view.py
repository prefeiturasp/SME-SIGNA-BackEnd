"""Testes para a view de pré-visualização do texto SEI."""

import pytest
from django.contrib.auth import get_user_model
from rest_framework import status
from rest_framework.test import APIClient

from apps.designacao.models.ato_administrativo import AtoAdministrativo
from apps.gestao.__tests__.factories import criar_modelo_portaria

User = get_user_model()

URL = "/api/designacao/textos-sei/preview/"


@pytest.fixture
def client():
    """Cliente de API sem autenticação."""
    return APIClient()


@pytest.fixture
def user(db):
    """Usuário de teste."""
    return User.objects.create_user(username="usuario", password="senha123")


@pytest.fixture
def auth_client(client, user):
    """Cliente de API autenticado."""
    client.force_authenticate(user=user)
    return client


@pytest.mark.django_db
def test_preview_retorna_texto_gerado_e_modelo_usado(auth_client):
    """Verifica que a prévia retorna o texto renderizado e o id do modelo."""
    modelo = criar_modelo_portaria(
        tipo_portaria=AtoAdministrativo.Tipo.DESIGNACAO,
        texto_portaria="Designa {{NOME_SERVIDOR}}.",
    )

    response = auth_client.post(
        URL,
        {
            "tipo_portaria": AtoAdministrativo.Tipo.DESIGNACAO,
            "dados": {"NOME_SERVIDOR": "João da Silva"},
        },
        format="json",
    )

    assert response.status_code == status.HTTP_200_OK
    assert response.data["modelo_portaria_id"] == modelo.pk
    assert response.data["texto"] == "Designa João da Silva."


@pytest.mark.django_db
def test_preview_considera_tipo_ato_pai_para_apostila(auth_client):
    """Verifica que apostila usa o modelo do tipo de ato pai informado."""
    criar_modelo_portaria(
        tipo_portaria=AtoAdministrativo.Tipo.APOSTILA,
        tipo_ato_pai=AtoAdministrativo.Tipo.CESSACAO,
        texto_portaria="Apostila de cessação.",
    )

    response = auth_client.post(
        URL,
        {
            "tipo_portaria": AtoAdministrativo.Tipo.APOSTILA,
            "tipo_ato_pai": AtoAdministrativo.Tipo.CESSACAO,
            "dados": {},
        },
        format="json",
    )

    assert response.status_code == status.HTTP_200_OK
    assert response.data["texto"] == "Apostila de cessação."


@pytest.mark.django_db
def test_preview_retorna_400_sem_modelo_ativo(auth_client):
    """Verifica erro 400 quando não há modelo ativo para o tipo informado."""
    response = auth_client.post(
        URL,
        {"tipo_portaria": AtoAdministrativo.Tipo.CESSACAO, "dados": {}},
        format="json",
    )

    assert response.status_code == status.HTTP_400_BAD_REQUEST


@pytest.mark.django_db
def test_preview_retorna_400_para_tipo_portaria_invalido(auth_client):
    """Verifica erro 400 quando tipo_portaria não é um tipo de ato válido."""
    response = auth_client.post(
        URL,
        {"tipo_portaria": "TIPO_INEXISTENTE", "dados": {}},
        format="json",
    )

    assert response.status_code == status.HTTP_400_BAD_REQUEST


def test_preview_exige_autenticacao(client, db):
    """Verifica que a rota exige usuário autenticado."""
    response = client.post(
        URL,
        {"tipo_portaria": AtoAdministrativo.Tipo.DESIGNACAO, "dados": {}},
        format="json",
    )

    assert response.status_code == status.HTTP_401_UNAUTHORIZED
