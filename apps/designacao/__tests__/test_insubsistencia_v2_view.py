"""Testes para a view v2 de insubsistência."""

import secrets

import pytest
from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework.test import APIClient

from apps.designacao.__tests__.factories import (
    criar_ato_apostila,
    criar_ato_cessacao,
    criar_ato_designacao,
    criar_ato_insubsistencia,
)
from apps.designacao.models.ato_administrativo import AtoAdministrativo
from apps.designacao.models.insubsistencia_apostila_detalhe import (
    InsubsistenciaApostilaDetalhe,
)

User = get_user_model()


@pytest.fixture
def auth_client(db):
    """Método auth client."""
    password = secrets.token_urlsafe(16)
    user = User.objects.create_user(
        username="test_insub_v2", password=password
    )
    client = APIClient()
    client.force_authenticate(user=user)
    return client


def _payload(ato_pai_id, **kwargs):
    """Método auxiliar para payload."""
    base = {
        "ato_pai": ato_pai_id,
        "numero_portaria": "12345",
        "ano_vigente": "2024",
        "sei_numero": "999999",
        "observacoes": "Criada via teste v2",
    }
    base.update(kwargs)
    return base


@pytest.mark.django_db
def test_create_insubsistencia_v2_de_designacao(auth_client):
    """Verifica create insubsistencia v2 de designacao."""
    d = criar_ato_designacao()
    url = reverse("designacao_v2:insubsistencias")
    response = auth_client.post(url, data=_payload(d.id), format="json")
    assert response.status_code == 201
    assert AtoAdministrativo.objects.filter(
        tipo=AtoAdministrativo.Tipo.INSUBSISTENCIA, ato_pai=d
    ).exists()


@pytest.mark.django_db
def test_create_insubsistencia_v2_registra_criado_por(auth_client):
    """Verifica que a insubsistencia criada registra o usuario responsavel."""
    d = criar_ato_designacao()
    user = User.objects.get(username="test_insub_v2")

    url = reverse("designacao_v2:insubsistencias")
    response = auth_client.post(url, data=_payload(d.id), format="json")

    assert response.status_code == 201
    insub = AtoAdministrativo.objects.get(
        tipo=AtoAdministrativo.Tipo.INSUBSISTENCIA, ato_pai=d
    )
    assert insub.criado_por_id == user.id


@pytest.mark.django_db
def test_create_insubsistencia_v2_de_cessacao(auth_client):
    """Verifica create insubsistencia v2 de cessacao."""
    d = criar_ato_designacao()
    c = criar_ato_cessacao(d)
    url = reverse("designacao_v2:insubsistencias")
    response = auth_client.post(url, data=_payload(c.id), format="json")
    assert response.status_code == 201
    assert AtoAdministrativo.objects.filter(
        tipo=AtoAdministrativo.Tipo.INSUBSISTENCIA, ato_pai=c
    ).exists()


@pytest.mark.django_db
def test_create_insubsistencia_v2_ato_pai_invalido(auth_client):
    """Verifica create insubsistencia v2 ato pai invalido."""
    url = reverse("designacao_v2:insubsistencias")
    response = auth_client.post(url, data=_payload(9999), format="json")
    assert response.status_code == 400
    assert "ato_pai" in response.data


@pytest.mark.django_db
def test_create_insubsistencia_v2_duplicada_rejeita(auth_client):
    """Verifica create insubsistencia v2 duplicada rejeita."""
    d = criar_ato_designacao()
    criar_ato_insubsistencia(d)
    d.ativo = False
    d.save(update_fields=["ativo"])
    url = reverse("designacao_v2:insubsistencias")
    response = auth_client.post(url, data=_payload(d.id), format="json")
    assert response.status_code == 400


@pytest.mark.django_db
def test_create_insubsistencia_v2_marca_pai_como_inativo(auth_client):
    """Verifica create insubsistencia v2 marca pai como inativo."""
    d = criar_ato_designacao()
    url = reverse("designacao_v2:insubsistencias")
    auth_client.post(url, data=_payload(d.id), format="json")
    d.refresh_from_db()
    assert not d.ativo


@pytest.mark.django_db
def test_list_insubsistencias_v2(auth_client):
    """Verifica list insubsistencias v2."""
    d = criar_ato_designacao()
    criar_ato_insubsistencia(d)
    url = reverse("designacao_v2:insubsistencias")
    response = auth_client.get(url)
    assert response.status_code == 200
    assert response.data["count"] >= 1


@pytest.mark.django_db
def test_retrieve_insubsistencia_v2(auth_client):
    """Verifica retrieve insubsistencia v2."""
    d = criar_ato_designacao()
    insub = criar_ato_insubsistencia(d)
    url = reverse("designacao_v2:insubsistencia-detail", args=[insub.id])
    response = auth_client.get(url)
    assert response.status_code == 200
    assert response.data["id"] == insub.id


@pytest.mark.django_db
def test_retrieve_insubsistencia_v2_nao_encontrada(auth_client):
    """Verifica retrieve insubsistencia v2 nao encontrada."""
    url = reverse("designacao_v2:insubsistencia-detail", args=[9999])
    response = auth_client.get(url)
    assert response.status_code == 404


@pytest.mark.django_db
def test_destroy_insubsistencia_v2_restaura_pai(auth_client):
    """Verifica destroy insubsistencia v2 restaura pai."""
    d = criar_ato_designacao()
    insub = criar_ato_insubsistencia(d)
    d.ativo = False
    d.save(update_fields=["ativo"])

    url = reverse("designacao_v2:insubsistencia-detail", args=[insub.id])
    response = auth_client.delete(url)

    assert response.status_code == 204
    assert not AtoAdministrativo.objects.filter(pk=insub.pk).exists()
    d.refresh_from_db()
    assert d.ativo


@pytest.mark.django_db
def test_create_insubsistencia_v2_de_apostila_cria_detalhe(auth_client):
    """Insubsistência de apostila cria InsubsistenciaApostilaDetalhe."""
    d = criar_ato_designacao()
    apostila = criar_ato_apostila(d)
    url = reverse("designacao_v2:insubsistencias")
    payload = _payload(
        apostila.id, texto_apostila="Texto de anulação da apostila"
    )
    response = auth_client.post(url, data=payload, format="json")
    assert response.status_code == 201
    insub = AtoAdministrativo.objects.get(
        tipo=AtoAdministrativo.Tipo.INSUBSISTENCIA, ato_pai=apostila
    )
    assert InsubsistenciaApostilaDetalhe.objects.filter(ato=insub).exists()
    assert (
        InsubsistenciaApostilaDetalhe.objects.get(ato=insub).texto
        == "Texto de anulação da apostila"
    )


@pytest.mark.django_db
def test_create_insubsistencia_v2_de_apostila_retorna_texto(auth_client):
    """Resposta da insubsistência de apostila inclui texto_apostila."""
    d = criar_ato_designacao()
    apostila = criar_ato_apostila(d)
    url = reverse("designacao_v2:insubsistencias")
    payload = _payload(apostila.id, texto_apostila="Motivo formal da anulação")
    response = auth_client.post(url, data=payload, format="json")
    assert response.status_code == 201
    assert response.data["texto_apostila"] == "Motivo formal da anulação"


@pytest.mark.django_db
def test_insubsistencia_v2_de_designacao_texto_apostila_nulo(auth_client):
    """Insubsistência de designação retorna texto_apostila como None."""
    d = criar_ato_designacao()
    url = reverse("designacao_v2:insubsistencias")
    response = auth_client.post(url, data=_payload(d.id), format="json")
    assert response.status_code == 201
    assert response.data["texto_apostila"] is None


@pytest.mark.django_db
def test_retrieve_insubsistencia_v2_apostila_exibe_texto(auth_client):
    """Retrieve de insubsistência de apostila exibe texto_apostila."""
    d = criar_ato_designacao()
    apostila = criar_ato_apostila(d)
    insub = criar_ato_insubsistencia(
        apostila, texto_apostila="Texto via factory"
    )
    apostila.ativo = False
    apostila.save(update_fields=["ativo"])
    url = reverse("designacao_v2:insubsistencia-detail", args=[insub.id])
    response = auth_client.get(url)
    assert response.status_code == 200
    assert response.data["texto_apostila"] == "Texto via factory"


@pytest.mark.django_db
def test_buscar_por_portaria_encontra_insubsistencia(auth_client):
    """Verifica que a busca por portaria encontra a insubsistência."""
    d = criar_ato_designacao()
    cessacao = criar_ato_cessacao(d)
    insub = criar_ato_insubsistencia(
        cessacao, numero_portaria="654", ano_vigente="2025"
    )

    url = reverse("designacao_v2:insubsistencia-buscar-por-portaria")
    response = auth_client.get(url, {"portaria": "654"})

    assert response.status_code == 200
    assert response.data["id"] == insub.id
    assert response.data["ato_pai_id"] == cessacao.id


@pytest.mark.django_db
def test_buscar_por_portaria_insubsistencia_nao_encontrada(auth_client):
    """Verifica 404 quando a portaria não corresponde a nenhuma insubsistência."""  # noqa: E501
    url = reverse("designacao_v2:insubsistencia-buscar-por-portaria")
    response = auth_client.get(url, {"portaria": "inexistente"})

    assert response.status_code == 404


@pytest.mark.django_db
def test_buscar_por_portaria_insubsistencia_sem_parametro(auth_client):
    """Verifica 400 quando o parâmetro portaria não é informado."""
    url = reverse("designacao_v2:insubsistencia-buscar-por-portaria")
    response = auth_client.get(url)

    assert response.status_code == 400
