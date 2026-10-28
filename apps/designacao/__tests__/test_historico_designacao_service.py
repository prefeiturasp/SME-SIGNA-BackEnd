"""Testes do serviço de histórico de designações por unidade."""

import datetime

import pytest
from django.http import QueryDict
from rest_framework.exceptions import ValidationError

from apps.designacao.__tests__.factories import (
    criar_ato_apostila,
    criar_ato_cessacao,
    criar_ato_designacao,
)
from apps.designacao.models.ato_administrativo import AtoAdministrativo
from apps.designacao.services.historico_designacao_service import (
    HistoricoDesignacaoService,
)
from apps.gestao.models.cargo_base import CargoBase

pytestmark = pytest.mark.django_db

UE = "019453"


class TestVariantesCodigoUe:
    """Formas aceitas do código EOL da unidade."""

    @pytest.mark.parametrize(
        ("codigo", "esperado"),
        [
            ("019453", {"019453", "19453"}),
            ("  19453 ", {"19453", "019453"}),
            ("108", {"108", "000108"}),
            ("000108", {"000108", "108"}),
            ("UE-1", {"UE-1"}),
            ("000", {"000"}),
            ("0", {"0"}),
            ("", set()),
            ("   ", set()),
        ],
    )
    def test_variantes(self, codigo, esperado):
        assert (
            HistoricoDesignacaoService._variantes_codigo_ue(codigo) == esperado
        )


class TestListarPorUe:
    """Consulta das designações e da hierarquia de atos derivados."""

    def test_ue_sem_designacao_devolve_lista_vazia(self):
        criar_ato_designacao(ue="099999")

        assert HistoricoDesignacaoService.listar_por_ue(UE) == []

    def test_encontra_a_ue_com_ou_sem_zeros_a_esquerda(self):
        ato = criar_ato_designacao(ue="19453")

        encontrados = HistoricoDesignacaoService.listar_por_ue("019453")

        assert [item.pk for item in encontrados] == [ato.pk]

    def test_ordena_pela_data_de_inicio_e_desempata_pela_criacao(self):
        antiga = criar_ato_designacao(
            ue=UE, data_inicio=datetime.date(2024, 1, 1)
        )
        recente = criar_ato_designacao(
            ue=UE, data_inicio=datetime.date(2024, 6, 1)
        )
        mesma_data = criar_ato_designacao(
            ue=UE, data_inicio=datetime.date(2024, 1, 1)
        )
        AtoAdministrativo.objects.filter(pk=antiga.pk).update(
            criado_em=datetime.datetime(2024, 1, 2, tzinfo=datetime.UTC)
        )
        AtoAdministrativo.objects.filter(pk=mesma_data.pk).update(
            criado_em=datetime.datetime(2024, 1, 3, tzinfo=datetime.UTC)
        )

        encontrados = HistoricoDesignacaoService.listar_por_ue(UE)

        assert [item.pk for item in encontrados] == [
            recente.pk,
            mesma_data.pk,
            antiga.pk,
        ]

    def test_monta_os_filhos_em_memoria(self, django_assert_num_queries):
        designacao = criar_ato_designacao(ue=UE)
        cessacao = criar_ato_cessacao(designacao)
        apostila = criar_ato_apostila(cessacao)

        with django_assert_num_queries(1):
            [carregada] = HistoricoDesignacaoService.listar_por_ue(UE)

        with django_assert_num_queries(0):
            filhos = list(carregada.filhos.all())
            netos = list(filhos[0].filhos.all())
            vigente = carregada.esta_vigente

        assert [ato.pk for ato in filhos] == [cessacao.pk]
        assert [ato.pk for ato in netos] == [apostila.pk]
        assert vigente is False
        assert "texto_sei" in carregada.get_deferred_fields()

    def test_filtro_invalido_gera_erro(self):
        with pytest.raises(ValidationError):
            HistoricoDesignacaoService.listar_por_ue(
                UE, {"status_publicacao": "INVALIDO"}
            )

    def test_filtra_por_cargo_via_querydict(self):
        diretor = criar_ato_designacao(ue=UE, cargo_vaga=3360)
        criar_ato_designacao(ue=UE, cargo_vaga=3085)

        encontrados = HistoricoDesignacaoService.listar_por_ue(
            UE, QueryDict("cargo=3360")
        )

        assert [item.pk for item in encontrados] == [diretor.pk]

    def test_sem_cargo_de_vaga_nao_consulta_o_cadastro(
        self, django_assert_num_queries
    ):
        criar_ato_designacao(ue=UE, cargo_vaga=None)

        with django_assert_num_queries(1):
            [designacao] = HistoricoDesignacaoService.listar_por_ue(UE)

        assert designacao._cargo_por_codigo == {}

    def test_anexa_a_descricao_do_cargo_uma_unica_vez(self):
        CargoBase.objects.create(
            codigo_cargo="8801",
            descricao_completa="CARGO DE TESTE",
            descricao_resumida="Teste",
            grupamento=CargoBase.Grupamento.GESTORES_EDUCACAO,
            situacao_funcional=CargoBase.SituacaoFuncional.EFETIVO,
        )
        criar_ato_designacao(ue=UE, cargo_vaga=8801)
        criar_ato_designacao(ue=UE, cargo_vaga=1111)

        primeira, segunda = HistoricoDesignacaoService.listar_por_ue(UE)

        assert primeira._cargo_por_codigo is segunda._cargo_por_codigo
        assert primeira._cargo_por_codigo == {"8801": "CARGO DE TESTE"}

    def test_preencher_descricoes_de_lista_vazia_nao_consulta(
        self, django_assert_num_queries
    ):
        with django_assert_num_queries(0):
            HistoricoDesignacaoService._preencher_descricoes_de_cargo([])
