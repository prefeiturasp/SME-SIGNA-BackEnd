"""Testes para a view de designação.

"""

import secrets

import pytest
from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework.request import Request
from rest_framework.test import APIClient, APIRequestFactory

from apps.designacao.__tests__.factories import criar_ato_designacao
from apps.designacao.api.views.designacao import DesignacaoPagination
from apps.designacao.models.ato_administrativo import AtoAdministrativo
from apps.designacao.models.designacao_detalhe import DesignacaoDetalhe

User = get_user_model()


@pytest.fixture
def auth_client(db):
    """Método auth client."""
    password = secrets.token_urlsafe(16)
    user = User.objects.create_user(username="test", password=password)
    client = APIClient()
    client.force_authenticate(user=user)
    return client


def _bulk_criar_designacoes(n):
    """Método auxiliar para bulk criar designacoes."""
    atos = AtoAdministrativo.objects.bulk_create(
        [
            AtoAdministrativo(
                tipo=AtoAdministrativo.Tipo.DESIGNACAO,
                numero_portaria="123",
                ano_vigente="2024",
                sei_numero=f"SEI-{i}",
            )
            for i in range(n)
        ]
    )
    DesignacaoDetalhe.objects.bulk_create(
        [
            DesignacaoDetalhe(
                ato=a,
                dre_nome="DRE TESTE",
                unidade_proponente="UP",
                codigo_hierarquico="1",
                indicado_nome_civil="Nome",
                indicado_nome_servidor="Nome",
                indicado_rf=str(i).zfill(7),
                indicado_vinculo=1,
                indicado_cargo_base="Cargo",
                indicado_lotacao="Lotacao",
                indicado_local_exercicio="Local",
                data_inicio="2024-01-01",
                tipo_vaga="VAGO",
            )
            for i, a in enumerate(atos)
        ]
    )
    return atos


@pytest.mark.django_db
def test_list_without_pagination_effective(auth_client, monkeypatch):
    """Verifica list without pagination effective."""
    for _ in range(3):
        criar_ato_designacao()

    from apps.designacao.api.views.designacao import DesignacaoViewSet

    monkeypatch.setattr(
        DesignacaoViewSet, "paginate_queryset", lambda self, queryset: None
    )

    url = reverse("designacao_v2:designacoes")
    response = auth_client.get(url)

    assert response.status_code == 200
    assert isinstance(response.data, list)
    assert len(response.data) == 3


@pytest.mark.django_db
def test_list_designacoes_sem_filtro_limita_1000(auth_client):
    """Verifica list designacoes sem filtro limita 1000."""
    _bulk_criar_designacoes(1100)

    url = reverse("designacao_v2:designacoes")
    response = auth_client.get(url)

    assert response.status_code == 200
    assert response.data["count"] == 1000


@pytest.mark.django_db
def test_list_designacoes_no_pagination_remove_limite(auth_client):
    """Verifica list designacoes no pagination remove limite."""
    _bulk_criar_designacoes(1100)

    url = reverse("designacao_v2:designacoes")
    response = auth_client.get(url, {"no_pagination": "true"})

    assert response.status_code == 200
    assert isinstance(response.data, list)
    assert len(response.data) == 1100


@pytest.mark.django_db
def test_paginate_queryset_retorna_none_quando_no_pagination_true():
    """Verifica paginate queryset retorna none quando no pagination true."""
    paginator = DesignacaoPagination()
    url = reverse("designacao_v2:designacoes")
    request = Request(APIRequestFactory().get(url, {"no_pagination": "true"}))

    page = paginator.paginate_queryset(
        AtoAdministrativo.objects.none(), request
    )

    assert page is None


@pytest.mark.django_db
def test_create_designacao_registra_criado_por(auth_client):
    """Verifica que a designação criada registra o usuario responsavel."""
    user = User.objects.get(username="test")

    payload = {
        "numero_portaria": "555",
        "ano_vigente": "2024",
        "sei_numero": "SEI-D1",
        "dre_nome": "DRE Teste",
        "unidade_proponente": "Escola Teste",
        "codigo_hierarquico": "001",
        "indicado_nome_civil": "",
        "indicado_nome_servidor": "Nome Servidor",
        "indicado_rf": "1234567",
        "indicado_vinculo": 1,
        "indicado_cargo_base": "Cargo Base",
        "indicado_lotacao": "Lotacao",
        "indicado_local_exercicio": "Local",
        "data_inicio": "2024-01-01",
        "tipo_vaga": DesignacaoDetalhe.TipoVaga.VAGO,
    }

    url = reverse("designacao_v2:designacoes")
    response = auth_client.post(url, data=payload, format="json")

    assert response.status_code == 201
    ato = AtoAdministrativo.objects.get(tipo=AtoAdministrativo.Tipo.DESIGNACAO)
    assert ato.criado_por_id == user.id


@pytest.mark.django_db
def test_destroy_designacao(auth_client):
    """Verifica destroy designacao."""
    ato = criar_ato_designacao()

    url = reverse("designacao_v2:designacao-detail", args=[ato.id])
    response = auth_client.delete(url)

    assert response.status_code == 204
    assert not AtoAdministrativo.objects.filter(pk=ato.pk).exists()


@pytest.mark.django_db
def test_cargos_base_pareados_endpoint(auth_client):
    """Verifica cargos base pareados endpoint."""
    url = reverse("designacao_v2:cargos-base-pareados")
    response = auth_client.get(url)

    assert response.status_code == 200
    assert isinstance(response.data, list)


@pytest.mark.django_db
def test_cargos_sobrepostos_pareados_endpoint(auth_client):
    """Verifica cargos sobrepostos pareados endpoint."""
    url = reverse("designacao_v2:cargos-sobrepostos-pareados")
    response = auth_client.get(url)

    assert response.status_code == 200
    assert isinstance(response.data, list)


@pytest.mark.django_db
def test_buscar_por_portaria_encontra_designacao(auth_client):
    """Verifica que a busca por portaria encontra a designação correta."""
    criar_ato_designacao(numero_portaria="321", ano_vigente="2025")
    ato = criar_ato_designacao(numero_portaria="999", ano_vigente="2025")

    url = reverse("designacao_v2:designacao-buscar-por-portaria")
    response = auth_client.get(url, {"portaria": "999"})

    assert response.status_code == 200
    assert response.data["id"] == ato.id
    assert response.data["numero_portaria"] == "999"


@pytest.mark.django_db
def test_buscar_por_portaria_designacao_nao_encontrada(auth_client):
    """Verifica 404 quando a portaria não corresponde a nenhuma designação."""
    url = reverse("designacao_v2:designacao-buscar-por-portaria")
    response = auth_client.get(url, {"portaria": "inexistente"})

    assert response.status_code == 404


@pytest.mark.django_db
def test_buscar_por_portaria_designacao_sem_parametro(auth_client):
    """Verifica 400 quando o parâmetro portaria não é informado."""
    url = reverse("designacao_v2:designacao-buscar-por-portaria")
    response = auth_client.get(url)

    assert response.status_code == 400
