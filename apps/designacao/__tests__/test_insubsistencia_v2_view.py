"""Testes para a view v2 de insubsistência.

"""

import secrets
import pytest
from django.urls import reverse
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient

from apps.designacao.models.ato_administrativo import AtoAdministrativo
from apps.designacao.__tests__.factories import (
    criar_ato_designacao,
    criar_ato_cessacao,
    criar_ato_insubsistencia,
)

User = get_user_model()


@pytest.fixture
def auth_client(db):
    """Método auth client."""
    password = secrets.token_urlsafe(16)
    user = User.objects.create_user(username='test_insub_v2', password=password)
    client = APIClient()
    client.force_authenticate(user=user)
    return client


def _payload(ato_pai_id, **kwargs):
    """Método auxiliar para payload."""
    base = {
        'ato_pai': ato_pai_id,
        'numero_portaria': '12345',
        'ano_vigente': '2024',
        'sei_numero': '999999',
        'observacoes': 'Criada via teste v2',
    }
    base.update(kwargs)
    return base


@pytest.mark.django_db
def test_create_insubsistencia_v2_de_designacao(auth_client):
    """Verifica create insubsistencia v2 de designacao."""
    d = criar_ato_designacao()
    url = reverse('designacao_v2:insubsistencias')
    response = auth_client.post(url, data=_payload(d.id), format='json')
    assert response.status_code == 201
    assert AtoAdministrativo.objects.filter(
        tipo=AtoAdministrativo.Tipo.INSUBSISTENCIA, ato_pai=d
    ).exists()


@pytest.mark.django_db
def test_create_insubsistencia_v2_de_cessacao(auth_client):
    """Verifica create insubsistencia v2 de cessacao."""
    d = criar_ato_designacao()
    c = criar_ato_cessacao(d)
    url = reverse('designacao_v2:insubsistencias')
    response = auth_client.post(url, data=_payload(c.id), format='json')
    assert response.status_code == 201
    assert AtoAdministrativo.objects.filter(
        tipo=AtoAdministrativo.Tipo.INSUBSISTENCIA, ato_pai=c
    ).exists()


@pytest.mark.django_db
def test_create_insubsistencia_v2_ato_pai_invalido(auth_client):
    """Verifica create insubsistencia v2 ato pai invalido."""
    url = reverse('designacao_v2:insubsistencias')
    response = auth_client.post(url, data=_payload(9999), format='json')
    assert response.status_code == 400
    assert 'ato_pai' in response.data


@pytest.mark.django_db
def test_create_insubsistencia_v2_duplicada_rejeita(auth_client):
    """Verifica create insubsistencia v2 duplicada rejeita."""
    d = criar_ato_designacao()
    criar_ato_insubsistencia(d)
    d.ativo = False
    d.save(update_fields=['ativo'])
    url = reverse('designacao_v2:insubsistencias')
    response = auth_client.post(url, data=_payload(d.id), format='json')
    assert response.status_code == 400


@pytest.mark.django_db
def test_create_insubsistencia_v2_marca_pai_como_inativo(auth_client):
    """Verifica create insubsistencia v2 marca pai como inativo."""
    d = criar_ato_designacao()
    url = reverse('designacao_v2:insubsistencias')
    auth_client.post(url, data=_payload(d.id), format='json')
    d.refresh_from_db()
    assert not d.ativo


@pytest.mark.django_db
def test_list_insubsistencias_v2(auth_client):
    """Verifica list insubsistencias v2."""
    d = criar_ato_designacao()
    criar_ato_insubsistencia(d)
    url = reverse('designacao_v2:insubsistencias')
    response = auth_client.get(url)
    assert response.status_code == 200
    assert response.data['count'] >= 1


@pytest.mark.django_db
def test_retrieve_insubsistencia_v2(auth_client):
    """Verifica retrieve insubsistencia v2."""
    d = criar_ato_designacao()
    insub = criar_ato_insubsistencia(d)
    url = reverse('designacao_v2:insubsistencia-detail', args=[insub.id])
    response = auth_client.get(url)
    assert response.status_code == 200
    assert response.data['id'] == insub.id


@pytest.mark.django_db
def test_retrieve_insubsistencia_v2_nao_encontrada(auth_client):
    """Verifica retrieve insubsistencia v2 nao encontrada."""
    url = reverse('designacao_v2:insubsistencia-detail', args=[9999])
    response = auth_client.get(url)
    assert response.status_code == 404


@pytest.mark.django_db
def test_destroy_insubsistencia_v2_restaura_pai(auth_client):
    """Verifica destroy insubsistencia v2 restaura pai."""
    d = criar_ato_designacao()
    insub = criar_ato_insubsistencia(d)
    d.ativo = False
    d.save(update_fields=['ativo'])

    url = reverse('designacao_v2:insubsistencia-detail', args=[insub.id])
    response = auth_client.delete(url)

    assert response.status_code == 204
    assert not AtoAdministrativo.objects.filter(pk=insub.pk).exists()
    d.refresh_from_db()
    assert d.ativo
