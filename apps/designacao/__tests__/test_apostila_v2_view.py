import secrets
import pytest
from django.urls import reverse
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient

from apps.designacao.models.ato_administrativo import AtoAdministrativo
from apps.designacao.__tests__.factories import (
    criar_ato_designacao,
    criar_ato_cessacao,
    criar_ato_apostila,
)

User = get_user_model()


@pytest.fixture
def auth_client(db):
    password = secrets.token_urlsafe(16)
    user = User.objects.create_user(username='test_apostila_v2', password=password)
    client = APIClient()
    client.force_authenticate(user=user)
    return client


def _payload(ato_pai_id, **kwargs):
    base = {
        'ato_pai': ato_pai_id,
        'sei_numero': '99999',
        'observacao': 'Apostila via v2',
    }
    base.update(kwargs)
    return base


@pytest.mark.django_db
def test_create_apostila_v2_em_designacao(auth_client):
    designacao = criar_ato_designacao()

    url = reverse('designacao_v2:apostilas')
    response = auth_client.post(url, data=_payload(designacao.id), format='json')

    assert response.status_code == 201
    assert AtoAdministrativo.objects.filter(
        tipo=AtoAdministrativo.Tipo.APOSTILA, ato_pai=designacao
    ).exists()


@pytest.mark.django_db
def test_create_apostila_v2_em_cessacao(auth_client):
    designacao = criar_ato_designacao()
    cessacao = criar_ato_cessacao(designacao)

    url = reverse('designacao_v2:apostilas')
    response = auth_client.post(url, data=_payload(cessacao.id), format='json')

    assert response.status_code == 201
    assert AtoAdministrativo.objects.filter(
        tipo=AtoAdministrativo.Tipo.APOSTILA, ato_pai=cessacao
    ).exists()


@pytest.mark.django_db
def test_create_apostila_v2_com_alteracoes(auth_client):
    designacao = criar_ato_designacao(numero_portaria='001')

    payload = _payload(designacao.id, alteracoes=[
        {'campo_alterado': 'numero_portaria', 'valor_novo': '999'},
    ])
    url = reverse('designacao_v2:apostilas')
    response = auth_client.post(url, data=payload, format='json')

    assert response.status_code == 201
    designacao.refresh_from_db()
    assert designacao.numero_portaria == '999'
    assert len(response.data['alteracoes']) == 1


@pytest.mark.django_db
def test_create_apostila_v2_ato_pai_invalido(auth_client):
    url = reverse('designacao_v2:apostilas')
    response = auth_client.post(url, data=_payload(9999), format='json')

    assert response.status_code == 400
    assert 'ato_pai' in response.data


@pytest.mark.django_db
def test_create_apostila_v2_segunda_apostila_permitida(auth_client):
    designacao = criar_ato_designacao()
    criar_ato_apostila(designacao)

    url = reverse('designacao_v2:apostilas')
    response = auth_client.post(url, data=_payload(designacao.id), format='json')

    assert response.status_code == 201


@pytest.mark.django_db
def test_create_apostila_v2_rejeita_designacao_cessada(auth_client):
    designacao = criar_ato_designacao()
    criar_ato_cessacao(designacao)

    url = reverse('designacao_v2:apostilas')
    response = auth_client.post(url, data=_payload(designacao.id), format='json')

    assert response.status_code == 400
    assert 'ato_pai' in response.data


@pytest.mark.django_db
def test_list_apostilas_v2(auth_client):
    designacao = criar_ato_designacao()
    criar_ato_apostila(designacao)

    url = reverse('designacao_v2:apostilas')
    response = auth_client.get(url)

    assert response.status_code == 200
    assert response.data['count'] >= 1


@pytest.mark.django_db
def test_retrieve_apostila_v2(auth_client):
    designacao = criar_ato_designacao()
    apostila = criar_ato_apostila(designacao)

    url = reverse('designacao_v2:apostila-detail', args=[apostila.id])
    response = auth_client.get(url)

    assert response.status_code == 200
    assert response.data['id'] == apostila.id


@pytest.mark.django_db
def test_retrieve_apostila_v2_nao_encontrada(auth_client):
    url = reverse('designacao_v2:apostila-detail', args=[9999])
    response = auth_client.get(url)

    assert response.status_code == 404


@pytest.mark.django_db
def test_destroy_apostila_v2(auth_client):
    designacao = criar_ato_designacao()
    apostila = criar_ato_apostila(designacao)

    url = reverse('designacao_v2:apostila-detail', args=[apostila.id])
    response = auth_client.delete(url)

    assert response.status_code == 204
    assert not AtoAdministrativo.objects.filter(pk=apostila.pk).exists()
