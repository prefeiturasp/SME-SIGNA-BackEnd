"""Testes para a view de cessação."""

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
        username="test_cessacao", password=password
    )
    client = APIClient()
    client.force_authenticate(user=user)
    return client


def _payload(ato_pai_id):
    """Método auxiliar para payload."""
    return {
        "ato_pai": ato_pai_id,
        "numero_portaria": "9999",
        "ano_vigente": "2024",
        "sei_numero": "SEI-C1",
        "a_pedido": True,
        "data_cessacao": "2024-06-01",
    }


@pytest.mark.django_db
def test_create_cessacao(auth_client):
    """Verifica create cessacao."""
    designacao = criar_ato_designacao()

    url = reverse("designacao:cessacoes")
    response = auth_client.post(
        url, data=_payload(designacao.id), format="json"
    )

    assert response.status_code == 201
    cessacao = AtoAdministrativo.objects.filter(
        tipo=AtoAdministrativo.Tipo.CESSACAO
    )
    assert cessacao.exists()
    assert (
        cessacao.get().status_publicacao
        == AtoAdministrativo.StatusPublicacao.NAO_PUBLICADO
    )


@pytest.mark.django_db
def test_create_cessacao_registra_criado_por(auth_client):
    """Verifica que a cessacao criada registra o usuario responsavel."""
    designacao = criar_ato_designacao()
    user = User.objects.get(username="test_cessacao")

    url = reverse("designacao:cessacoes")
    response = auth_client.post(
        url, data=_payload(designacao.id), format="json"
    )

    assert response.status_code == 201
    cessacao = AtoAdministrativo.objects.get(
        tipo=AtoAdministrativo.Tipo.CESSACAO
    )
    assert cessacao.criado_por_id == user.id


@pytest.mark.django_db
def test_create_cessacao_ato_pai_invalido(auth_client):
    """Verifica create cessacao ato pai invalido."""
    url = reverse("designacao:cessacoes")
    response = auth_client.post(url, data=_payload(9999), format="json")

    assert response.status_code == 400
    assert "ato_pai" in response.data


@pytest.mark.django_db
def test_create_cessacao_duplicada_rejeita(auth_client):
    """Verifica create cessacao duplicada rejeita."""
    designacao = criar_ato_designacao()
    criar_ato_cessacao(designacao)

    url = reverse("designacao:cessacoes")
    response = auth_client.post(
        url, data=_payload(designacao.id), format="json"
    )

    assert response.status_code == 400


@pytest.mark.django_db
def test_list_cessacoes(auth_client):
    """Verifica list cessacoes."""
    designacao = criar_ato_designacao()
    criar_ato_cessacao(designacao)

    url = reverse("designacao:cessacoes")
    response = auth_client.get(url)

    assert response.status_code == 200
    assert response.data["count"] >= 1


@pytest.mark.django_db
def test_retrieve_cessacao(auth_client):
    """Verifica retrieve cessacao."""
    designacao = criar_ato_designacao()
    cessacao = criar_ato_cessacao(designacao)

    url = reverse("designacao:cessacao-detail", args=[cessacao.id])
    response = auth_client.get(url)

    assert response.status_code == 200
    assert response.data["id"] == cessacao.id


@pytest.mark.django_db
def test_destroy_cessacao(auth_client):
    """Verifica destroy cessacao."""
    designacao = criar_ato_designacao()
    cessacao = criar_ato_cessacao(designacao)

    url = reverse("designacao:cessacao-detail", args=[cessacao.id])
    response = auth_client.delete(url)

    assert response.status_code == 204
    assert not AtoAdministrativo.objects.filter(pk=cessacao.pk).exists()


@pytest.mark.django_db
def test_buscar_por_portaria_encontra_cessacao(auth_client):
    """Verifica que a busca por portaria e ano encontra a cessação e o ato pai."""  # noqa: E501
    designacao = criar_ato_designacao()
    cessacao = criar_ato_cessacao(
        designacao, numero_portaria="777", ano_vigente="2025"
    )

    url = reverse("designacao:cessacao-buscar-por-portaria")
    response = auth_client.get(url, {"portaria": "777", "ano": "2025"})

    assert response.status_code == 200
    assert response.data["id"] == cessacao.id
    assert response.data["ato_pai_id"] == designacao.id


@pytest.mark.django_db
def test_buscar_por_portaria_cessacao_retorna_apostilas_ativas(auth_client):
    """Verifica que apostilas insubsistentes são excluídas da lista."""
    designacao = criar_ato_designacao()
    cessacao = criar_ato_cessacao(
        designacao, numero_portaria="778", ano_vigente="2025"
    )
    apostila_ativa = criar_ato_apostila(cessacao, sei_numero="SEI-ATIVA")
    apostila_anulada = criar_ato_apostila(cessacao, sei_numero="SEI-ANULADA")
    apostila_anulada.ativo = False
    apostila_anulada.save(update_fields=["ativo"])

    url = reverse("designacao:cessacao-buscar-por-portaria")
    response = auth_client.get(url, {"portaria": "778", "ano": "2025"})

    assert response.status_code == 200
    ids_retornados = {a["id"] for a in response.data["apostilas"]}
    assert ids_retornados == {apostila_ativa.id}


@pytest.mark.django_db
def test_buscar_por_portaria_cessacao_nao_encontrada(auth_client):
    """Verifica 404 quando a portaria não corresponde a nenhuma cessação."""
    url = reverse("designacao:cessacao-buscar-por-portaria")
    response = auth_client.get(url, {"portaria": "inexistente", "ano": "2025"})

    assert response.status_code == 404


@pytest.mark.django_db
def test_buscar_por_portaria_cessacao_ano_diferente_nao_encontrada(
    auth_client,
):
    """Verifica 404 quando a portaria existe mas em outro ano."""
    designacao = criar_ato_designacao()
    criar_ato_cessacao(designacao, numero_portaria="777", ano_vigente="2024")

    url = reverse("designacao:cessacao-buscar-por-portaria")
    response = auth_client.get(url, {"portaria": "777", "ano": "2025"})

    assert response.status_code == 404


@pytest.mark.django_db
def test_buscar_por_portaria_cessacao_sem_parametro_portaria(auth_client):
    """Verifica 400 quando o parâmetro portaria não é informado."""
    url = reverse("designacao:cessacao-buscar-por-portaria")
    response = auth_client.get(url, {"ano": "2025"})

    assert response.status_code == 400


@pytest.mark.django_db
def test_buscar_por_portaria_cessacao_sem_parametro_ano(auth_client):
    """Verifica 400 quando o parâmetro ano não é informado."""
    url = reverse("designacao:cessacao-buscar-por-portaria")
    response = auth_client.get(url, {"portaria": "777"})

    assert response.status_code == 400
