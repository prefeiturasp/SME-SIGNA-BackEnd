"""Testes para o viewset de atos administrativos da API."""

import secrets
from datetime import date

import pytest
from django.contrib.auth import get_user_model
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import filters
from rest_framework.test import APIClient

from apps.designacao.api.filters.ato_administrativo_filter import (
    AtoAdministrativoFilter,
)
from apps.designacao.api.serializers.ato_administrativo_serializer import (
    AtoAdministrativoListSerializer,
)
from apps.designacao.api.views.ato_administrativo_view import (
    AtoAdministrativoListViewSet,
)
from apps.designacao.api.views.designacao_base import DesignacaoBasePagination
from apps.designacao.models.ato_administrativo import AtoAdministrativo
from apps.designacao.models.designacao_detalhe import DesignacaoDetalhe

User = get_user_model()


# ─── URLs ─────────────────────────────────────────────────────────────────────

URL_LIST = "/api/designacao/atos-administrativos/"


# ─── Fixtures ─────────────────────────────────────────────────────────────────


@pytest.fixture
def auth_client(db):
    """Cria um cliente autenticado para chamadas de API."""
    password = secrets.token_urlsafe(16)
    user = User.objects.create_user(
        username="test_ato_admin", password=password
    )
    client = APIClient()
    client.force_authenticate(user=user)
    return client


@pytest.fixture
def designacao_1(db):
    """Cria um ato de designação com status não publicado."""
    ato = AtoAdministrativo.objects.create(
        tipo="DESIGNACAO",
        numero_portaria="001/2024",
        ano_vigente="2024",
        sei_numero="6018.2024/0001234-5",
        doc=None,
        ativo=True,
        status_publicacao=AtoAdministrativo.StatusPublicacao.NAO_PUBLICADO,
    )
    DesignacaoDetalhe.objects.create(
        ato=ato,
        dre_nome="DRE BUTANTA",
        unidade_proponente="EMEF TESTE 1",
        codigo_hierarquico="108600",
        indicado_nome_servidor="MARIA SILVA",
        indicado_nome_civil="Maria da Silva",
        indicado_rf="12345678",
        indicado_vinculo=1,
        indicado_cargo_base="PROFESSOR DE EF I",
        indicado_lotacao="EMEF TESTE 1",
        indicado_cargo_sobreposto="DIRETOR DE ESCOLA",
        indicado_codigo_cargo_sobreposto=3360,
        indicado_local_exercicio="EMEF TESTE 1",
        data_inicio=date(2024, 1, 15),
        tipo_vaga="VAGO",
        cargo_vaga=3360,
        titular_nome_servidor="JOAO TITULAR",
        titular_nome_civil="Joao Titular",
        titular_rf="44445555",
        titular_vinculo=1,
        titular_cargo_base="PROFESSOR DE EF I",
        titular_lotacao="EMEF TESTE 1",
        titular_cargo_sobreposto="DIRETOR DE ESCOLA",
        titular_codigo_cargo_sobreposto=3360,
        titular_local_exercicio="EMEF TESTE 1",
    )
    return ato


@pytest.fixture
def designacao_2(db):
    """Cria um ato de designação com status publicado."""
    ato = AtoAdministrativo.objects.create(
        tipo="DESIGNACAO",
        numero_portaria="002/2024",
        ano_vigente="2024",
        sei_numero="6018.2024/0002345-6",
        doc="2024-10-10",
        ativo=True,
        status_publicacao=AtoAdministrativo.StatusPublicacao.PUBLICADO,
    )
    DesignacaoDetalhe.objects.create(
        ato=ato,
        dre_nome="DRE IPIRANGA",
        unidade_proponente="EMEF TESTE 2",
        codigo_hierarquico="108700",
        indicado_nome_servidor="PEDRO SOUZA",
        indicado_nome_civil="Pedro de Souza",
        indicado_rf="87654321",
        indicado_vinculo=1,
        indicado_cargo_base="PROFESSOR DE EF II",
        indicado_lotacao="EMEF TESTE 2",
        indicado_cargo_sobreposto="COORDENADOR PEDAGOGICO",
        indicado_codigo_cargo_sobreposto=3379,
        indicado_local_exercicio="EMEF TESTE 2",
        data_inicio=date(2024, 2, 1),
        tipo_vaga="DISPONIVEL",
        cargo_vaga=3379,
        titular_nome_servidor="ANA TITULAR",
        titular_nome_civil="Ana Titular",
        titular_rf="99990000",
        titular_vinculo=1,
        titular_cargo_base="PROFESSOR DE EF II",
        titular_lotacao="EMEF TESTE 2",
        titular_cargo_sobreposto="COORDENADOR PEDAGOGICO",
        titular_codigo_cargo_sobreposto=3379,
        titular_local_exercicio="EMEF TESTE 2",
    )
    return ato


# ─── Testes: GET /atos-administrativos/ ──────────────────────────────────────


@pytest.mark.django_db
class TestAtoAdministrativoListView:
    """Testa a rota de listagem de atos administrativos da API."""

    def test_configuracao_do_viewset(self):
        """Valida as configurações declaradas no viewset."""
        assert (
            AtoAdministrativoListViewSet.serializer_class
            == AtoAdministrativoListSerializer
        )
        assert (
            AtoAdministrativoListViewSet.pagination_class
            == DesignacaoBasePagination
        )
        assert (
            AtoAdministrativoListViewSet.filterset_class
            == AtoAdministrativoFilter
        )
        assert AtoAdministrativoListViewSet.filter_backends == [
            DjangoFilterBackend,
            filters.SearchFilter,
            filters.OrderingFilter,
        ]
        assert AtoAdministrativoListViewSet.search_fields == [
            "numero_portaria",
            "sei_numero",
            "designacao_detalhe__indicado_nome_servidor",
            "designacao_detalhe__indicado_nome_civil",
            "designacao_detalhe__indicado_rf",
        ]
        assert AtoAdministrativoListViewSet.ordering_fields == [
            "criado_em",
            "ano_vigente",
            "numero_portaria",
        ]
        assert AtoAdministrativoListViewSet.ordering == ["numero_portaria"]

    def test_retorna_200_com_estrutura_paginada(
        self, auth_client, designacao_1, designacao_2
    ):
        """Verifica resposta paginada padrão."""
        response = auth_client.get(URL_LIST)
        assert response.status_code == 200
        assert set(response.data.keys()) == {
            "count",
            "next",
            "previous",
            "results",
        }
        assert response.data["count"] == 2
        assert isinstance(response.data["results"], list)

    def test_retorna_lista_sem_paginacao(
        self, auth_client, designacao_1, designacao_2
    ):
        """Verifica retorno sem paginação."""
        response = auth_client.get(URL_LIST, {"no_pagination": "true"})
        assert response.status_code == 200
        assert isinstance(response.data, list)
        assert len(response.data) == 2

    def test_campos_retornados(self, auth_client, designacao_1):
        """Verifica campos do serializer no endpoint."""
        response = auth_client.get(URL_LIST, {"no_pagination": "true"})
        item = response.data[0]
        assert set(item.keys()) == {
            "id",
            "tipo_de_ato",
            "criado_em",
            "observacoes",
            "portaria",
            "ano_vigente",
            "nome",
            "status_publicacao",
            "sei_numero",
            "tipo",
            "cessacao",
            "apostilas",
            "insubsistencia",
        }

    def test_filtro_status_publicacao(
        self, auth_client, designacao_1, designacao_2
    ):
        """Verifica filtro por status_publicacao."""
        response = auth_client.get(
            URL_LIST,
            {
                "status_publicacao": AtoAdministrativo.StatusPublicacao.PUBLICADO,
                "no_pagination": "true",
            },
        )
        assert response.status_code == 200
        assert len(response.data) == 1
        assert response.data[0]["id"] == designacao_2.pk

    def test_filtro_portaria_exata(
        self, auth_client, designacao_1, designacao_2
    ):
        """Verifica filtro por portaria exata."""
        response = auth_client.get(
            URL_LIST, {"portaria": "001/2024", "no_pagination": "true"}
        )
        assert response.status_code == 200
        assert len(response.data) == 1
        assert response.data[0]["portaria"] == "001/2024"

    def test_filtro_nome_titular_e_indicado(
        self, auth_client, designacao_1, designacao_2
    ):
        """Verifica filtro por nome em titular e indicado."""
        response = auth_client.get(
            URL_LIST,
            {"nome_titular_e_indicado": "JOAO", "no_pagination": "true"},
        )
        assert response.status_code == 200
        assert len(response.data) == 1
        assert response.data[0]["id"] == designacao_1.pk

    def test_search_por_sei(self, auth_client, designacao_1, designacao_2):
        """Verifica busca textual via SearchFilter."""
        response = auth_client.get(
            URL_LIST, {"search": "0002345", "no_pagination": "true"}
        )
        assert response.status_code == 200
        assert len(response.data) == 1
        assert response.data[0]["sei_numero"] == "6018.2024/0002345-6"

    def test_ordering_numero_portaria_desc(
        self, auth_client, designacao_1, designacao_2
    ):
        """Verifica ordenação descendente por número da portaria."""
        response = auth_client.get(
            URL_LIST, {"ordering": "-numero_portaria", "no_pagination": "true"}
        )
        assert response.status_code == 200
        portarias = [item["portaria"] for item in response.data]
        assert portarias == ["002/2024", "001/2024"]
