"""Testes para a view de apostila."""

import secrets

import pytest
from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework.test import APIClient

from apps.designacao.__tests__.factories import (
    criar_ato_apostila,
    criar_ato_cessacao,
    criar_ato_designacao,
)
from apps.designacao.models.ato_administrativo import AtoAdministrativo

User = get_user_model()


@pytest.fixture
def auth_client(db):
    """Método auth client."""
    password = secrets.token_urlsafe(16)
    user = User.objects.create_user(
        username="test_apostila", password=password
    )
    client = APIClient()
    client.force_authenticate(user=user)
    return client


def _payload(ato_pai_id, **kwargs):
    """Método auxiliar para payload."""
    base = {
        "ato_pai": ato_pai_id,
        "sei_numero": "99999",
        "observacao": "Apostila via",
    }
    base.update(kwargs)
    return base


@pytest.mark.django_db
def test_create_apostila_em_designacao(auth_client):
    """Verifica create apostila em designacao."""
    designacao = criar_ato_designacao()

    url = reverse("designacao:apostilas")
    response = auth_client.post(
        url, data=_payload(designacao.id), format="json"
    )

    assert response.status_code == 201
    assert AtoAdministrativo.objects.filter(
        tipo=AtoAdministrativo.Tipo.APOSTILA, ato_pai=designacao
    ).exists()


@pytest.mark.django_db
def test_create_apostila_registra_criado_por(auth_client):
    """Verifica que a apostila criada registra o usuario responsavel."""
    designacao = criar_ato_designacao()
    user = User.objects.get(username="test_apostila")

    url = reverse("designacao:apostilas")
    response = auth_client.post(
        url, data=_payload(designacao.id), format="json"
    )

    assert response.status_code == 201
    apostila = AtoAdministrativo.objects.get(
        tipo=AtoAdministrativo.Tipo.APOSTILA, ato_pai=designacao
    )
    assert apostila.criado_por_id == user.id


@pytest.mark.django_db
def test_create_apostila_em_cessacao(auth_client):
    """Verifica create apostila em cessacao."""
    designacao = criar_ato_designacao()
    cessacao = criar_ato_cessacao(designacao)

    url = reverse("designacao:apostilas")
    response = auth_client.post(url, data=_payload(cessacao.id), format="json")

    assert response.status_code == 201
    assert AtoAdministrativo.objects.filter(
        tipo=AtoAdministrativo.Tipo.APOSTILA, ato_pai=cessacao
    ).exists()


@pytest.mark.django_db
def test_create_apostila_com_alteracoes(auth_client):
    """Verifica create apostila com alteracoes."""
    designacao = criar_ato_designacao(numero_portaria="001")

    payload = _payload(
        designacao.id,
        alteracoes=[
            {"campo_alterado": "numero_portaria", "valor_novo": "999"},
        ],
    )
    url = reverse("designacao:apostilas")
    response = auth_client.post(url, data=payload, format="json")

    assert response.status_code == 201
    designacao.refresh_from_db()
    assert designacao.numero_portaria == "999"
    assert len(response.data["alteracoes"]) == 1


@pytest.mark.django_db
def test_create_apostila_ato_pai_invalido(auth_client):
    """Verifica create apostila ato pai invalido."""
    url = reverse("designacao:apostilas")
    response = auth_client.post(url, data=_payload(9999), format="json")

    assert response.status_code == 400
    assert "ato_pai" in response.data


@pytest.mark.django_db
def test_create_apostila_segunda_apostila_nao_permitida(auth_client):
    """Verifica create apostila segunda apostila nao permitida."""
    designacao = criar_ato_designacao()
    criar_ato_apostila(designacao)

    url = reverse("designacao:apostilas")
    response = auth_client.post(
        url, data=_payload(designacao.id), format="json"
    )

    assert response.status_code == 400


@pytest.mark.django_db
def test_create_apostila_rejeita_designacao_cessada(auth_client):
    """Verifica create apostila rejeita designacao cessada."""
    designacao = criar_ato_designacao()
    criar_ato_cessacao(designacao)

    url = reverse("designacao:apostilas")
    response = auth_client.post(
        url, data=_payload(designacao.id), format="json"
    )

    assert response.status_code == 400
    assert "ato_pai" in response.data


@pytest.mark.django_db
def test_list_apostilas(auth_client):
    """Verifica list apostilas."""
    designacao = criar_ato_designacao()
    criar_ato_apostila(designacao)

    url = reverse("designacao:apostilas")
    response = auth_client.get(url)

    assert response.status_code == 200
    assert response.data["count"] >= 1


@pytest.mark.django_db
def test_retrieve_apostila(auth_client):
    """Verifica retrieve apostila."""
    designacao = criar_ato_designacao()
    apostila = criar_ato_apostila(designacao)

    url = reverse("designacao:apostila-detail", args=[apostila.id])
    response = auth_client.get(url)

    assert response.status_code == 200
    assert response.data["id"] == apostila.id


@pytest.mark.django_db
def test_retrieve_apostila_nao_encontrada(auth_client):
    """Verifica retrieve apostila nao encontrada."""
    url = reverse("designacao:apostila-detail", args=[9999])
    response = auth_client.get(url)

    assert response.status_code == 404


@pytest.mark.django_db
def test_destroy_apostila(auth_client):
    """Verifica destroy apostila."""
    designacao = criar_ato_designacao()
    apostila = criar_ato_apostila(designacao)

    url = reverse("designacao:apostila-detail", args=[apostila.id])
    response = auth_client.delete(url)

    assert response.status_code == 204
    assert not AtoAdministrativo.objects.filter(pk=apostila.pk).exists()
