"""Testes para a view v2 de cessação.

"""

import secrets
import pytest
from django.urls import reverse
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient

from apps.designacao.models.ato_administrativo import AtoAdministrativo
from apps.designacao.__tests__.factories import criar_ato_designacao, criar_ato_cessacao

User = get_user_model()


@pytest.fixture
def auth_client(db):
    """Método auth client."""
    password = secrets.token_urlsafe(16)
    user = User.objects.create_user(username='test_cessacao_v2', password=password)
    client = APIClient()
    client.force_authenticate(user=user)
    return client


def _payload(ato_pai_id):
    """Método auxiliar para payload."""
    return {
        'ato_pai': ato_pai_id,
        'numero_portaria': '9999',
        'ano_vigente': '2024',
        'sei_numero': 'SEI-C1',
        'a_pedido': True,
        'data_cessacao': '2024-06-01',
    }


@pytest.mark.django_db
def test_create_cessacao_v2(auth_client):
    """Verifica create cessacao v2."""
    designacao = criar_ato_designacao()

    url = reverse('designacao_v2:cessacoes')
    response = auth_client.post(url, data=_payload(designacao.id), format='json')

    assert response.status_code == 201
    assert AtoAdministrativo.objects.filter(tipo=AtoAdministrativo.Tipo.CESSACAO).exists()


@pytest.mark.django_db
def test_create_cessacao_v2_ato_pai_invalido(auth_client):
    """Verifica create cessacao v2 ato pai invalido."""
    url = reverse('designacao_v2:cessacoes')
    response = auth_client.post(url, data=_payload(9999), format='json')

    assert response.status_code == 400
    assert 'ato_pai' in response.data


@pytest.mark.django_db
def test_create_cessacao_v2_duplicada_rejeita(auth_client):
    """Verifica create cessacao v2 duplicada rejeita."""
    designacao = criar_ato_designacao()
    criar_ato_cessacao(designacao)

    url = reverse('designacao_v2:cessacoes')
    response = auth_client.post(url, data=_payload(designacao.id), format='json')

    assert response.status_code == 400


@pytest.mark.django_db
def test_list_cessacoes_v2(auth_client):
    """Verifica list cessacoes v2."""
    designacao = criar_ato_designacao()
    criar_ato_cessacao(designacao)

    url = reverse('designacao_v2:cessacoes')
    response = auth_client.get(url)

    assert response.status_code == 200
    assert response.data['count'] >= 1


@pytest.mark.django_db
def test_retrieve_cessacao_v2(auth_client):
    """Verifica retrieve cessacao v2."""
    designacao = criar_ato_designacao()
    cessacao = criar_ato_cessacao(designacao)

    url = reverse('designacao_v2:cessacao-detail', args=[cessacao.id])
    response = auth_client.get(url)

    assert response.status_code == 200
    assert response.data['id'] == cessacao.id


@pytest.mark.django_db
def test_destroy_cessacao_v2(auth_client):
    """Verifica destroy cessacao v2."""
    designacao = criar_ato_designacao()
    cessacao = criar_ato_cessacao(designacao)

    url = reverse('designacao_v2:cessacao-detail', args=[cessacao.id])
    response = auth_client.delete(url)

    assert response.status_code == 204
    assert not AtoAdministrativo.objects.filter(pk=cessacao.pk).exists()
