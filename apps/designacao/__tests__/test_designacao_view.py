import pytest
import secrets
from rest_framework.test import APIClient, APIRequestFactory
from rest_framework.request import Request
from django.urls import reverse
from django.contrib.auth import get_user_model

from apps.designacao.models.ato_administrativo import AtoAdministrativo
from apps.designacao.models.designacao_detalhe import DesignacaoDetalhe
from apps.designacao.api.views.designacao import DesignacaoPagination
from apps.designacao.__tests__.factories import criar_ato_designacao

User = get_user_model()


@pytest.fixture
def auth_client(db):
    password = secrets.token_urlsafe(16)
    user = User.objects.create_user(username='test', password=password)
    client = APIClient()
    client.force_authenticate(user=user)
    return client


def _bulk_criar_designacoes(n):
    atos = AtoAdministrativo.objects.bulk_create([
        AtoAdministrativo(
            tipo=AtoAdministrativo.Tipo.DESIGNACAO,
            numero_portaria='123',
            ano_vigente='2024',
            sei_numero=f'SEI-{i}',
        )
        for i in range(n)
    ])
    DesignacaoDetalhe.objects.bulk_create([
        DesignacaoDetalhe(
            ato=a,
            dre_nome='DRE TESTE',
            unidade_proponente='UP',
            codigo_hierarquico='1',
            indicado_nome_civil='Nome',
            indicado_nome_servidor='Nome',
            indicado_rf=str(i).zfill(7),
            indicado_vinculo=1,
            indicado_cargo_base='Cargo',
            indicado_lotacao='Lotacao',
            indicado_local_exercicio='Local',
            data_inicio='2024-01-01',
            tipo_vaga='VAGO',
        )
        for i, a in enumerate(atos)
    ])
    return atos


@pytest.mark.django_db
def test_list_without_pagination_effective(auth_client, monkeypatch):
    for _ in range(3):
        criar_ato_designacao()

    from apps.designacao.api.views.designacao import DesignacaoViewSet
    monkeypatch.setattr(DesignacaoViewSet, 'paginate_queryset', lambda self, queryset: None)

    url = reverse('designacao_v2:designacoes')
    response = auth_client.get(url)

    assert response.status_code == 200
    assert isinstance(response.data, list)
    assert len(response.data) == 3


@pytest.mark.django_db
def test_list_designacoes_sem_filtro_limita_1000(auth_client):
    _bulk_criar_designacoes(1100)

    url = reverse('designacao_v2:designacoes')
    response = auth_client.get(url)

    assert response.status_code == 200
    assert response.data['count'] == 1000


@pytest.mark.django_db
def test_list_designacoes_no_pagination_remove_limite(auth_client):
    _bulk_criar_designacoes(1100)

    url = reverse('designacao_v2:designacoes')
    response = auth_client.get(url, {'no_pagination': 'true'})

    assert response.status_code == 200
    assert isinstance(response.data, list)
    assert len(response.data) == 1100


@pytest.mark.django_db
def test_paginate_queryset_retorna_none_quando_no_pagination_true():
    paginator = DesignacaoPagination()
    url = reverse('designacao_v2:designacoes')
    request = Request(APIRequestFactory().get(url, {'no_pagination': 'true'}))

    page = paginator.paginate_queryset(AtoAdministrativo.objects.none(), request)

    assert page is None


@pytest.mark.django_db
def test_destroy_designacao(auth_client):
    ato = criar_ato_designacao()

    url = reverse('designacao_v2:designacao-detail', args=[ato.id])
    response = auth_client.delete(url)

    assert response.status_code == 204
    assert not AtoAdministrativo.objects.filter(pk=ato.pk).exists()


@pytest.mark.django_db
def test_cargos_base_pareados_endpoint(auth_client):
    url = reverse('designacao_v2:cargos-base-pareados')
    response = auth_client.get(url)

    assert response.status_code == 200
    assert isinstance(response.data, list)


@pytest.mark.django_db
def test_cargos_sobrepostos_pareados_endpoint(auth_client):
    url = reverse('designacao_v2:cargos-sobrepostos-pareados')
    response = auth_client.get(url)

    assert response.status_code == 200
    assert isinstance(response.data, list)
