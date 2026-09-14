"""Testes para serviço de designação."""

import datetime

import pytest
from rest_framework.exceptions import ValidationError

from apps.designacao.__tests__.factories import (
    criar_ato_cessacao,
    criar_ato_designacao,
)
from apps.designacao.models.ato_administrativo import AtoAdministrativo
from apps.designacao.models.designacao_detalhe import DesignacaoDetalhe
from apps.designacao.services.designacao_service import DesignacaoService


@pytest.mark.django_db
class TestDesignacaoService:
    """Testes para designacao service."""

    def test_criar_designacao(self):
        """Verifica criação de designação via service."""
        data = {
            "numero_portaria": "555",
            "ano_vigente": "2024",
            "sei_numero": "SEI-555",
            "dre_nome": "DRE Teste",
            "unidade_proponente": "Escola Teste",
            "codigo_hierarquico": "001",
            "indicado_nome_civil": "Nome Civil",
            "indicado_nome_servidor": "Nome Servidor",
            "indicado_rf": "1234567",
            "indicado_vinculo": 1,
            "indicado_cargo_base": "Cargo Base",
            "indicado_lotacao": "Lotacao",
            "indicado_local_exercicio": "Local",
            "data_inicio": datetime.date(2024, 1, 1),
            "tipo_vaga": DesignacaoDetalhe.TipoVaga.VAGO,
        }

        ato = DesignacaoService.criar(data)

        assert ato.tipo == AtoAdministrativo.Tipo.DESIGNACAO
        assert (
            ato.status_publicacao
            == AtoAdministrativo.StatusPublicacao.NAO_PUBLICADO
        )
        assert ato.numero_portaria == "555"
        assert ato.designacao_detalhe.indicado_nome_civil == "Nome Civil"

    def test_excluir_sem_dependentes(self):
        """Verifica exclusão de designação sem atos derivados."""
        designacao = criar_ato_designacao()

        DesignacaoService.excluir(designacao)

        assert not AtoAdministrativo.objects.filter(pk=designacao.pk).exists()

    def test_excluir_com_dependentes_gera_erro(self):
        """Verifica que exclusão é bloqueada quando há atos derivados."""
        designacao = criar_ato_designacao()
        criar_ato_cessacao(designacao)

        with pytest.raises(ValidationError):
            DesignacaoService.excluir(designacao)

        assert AtoAdministrativo.objects.filter(pk=designacao.pk).exists()

    def test_get_cargos_pareados_sucesso(self):
        """Verifica get cargos pareados sucesso."""
        criar_ato_designacao(
            indicado_codigo_cargo_base=1,
            indicado_cargo_base="Professor",
            titular_codigo_cargo_base=2,
            titular_cargo_base="Diretor",
        )
        criar_ato_designacao(
            indicado_codigo_cargo_base=3,
            indicado_cargo_base="Coordenador",
        )

        queryset = AtoAdministrativo.objects.filter(
            tipo=AtoAdministrativo.Tipo.DESIGNACAO
        )

        resultado = DesignacaoService.get_cargos_pareados(
            queryset,
            "designacao_detalhe__indicado_codigo_cargo_base",
            "designacao_detalhe__indicado_cargo_base",
            "designacao_detalhe__titular_codigo_cargo_base",
            "designacao_detalhe__titular_cargo_base",
        )

        assert resultado == [
            {"codigoCargo": 3, "nomeCargo": "Coordenador"},
            {"codigoCargo": 2, "nomeCargo": "Diretor"},
            {"codigoCargo": 1, "nomeCargo": "Professor"},
        ]

    def test_get_cargos_pareados_remove_invalidos(self):
        """Verifica get cargos pareados remove invalidos."""
        criar_ato_designacao(
            indicado_codigo_cargo_base=None,
            indicado_cargo_base="",
            titular_codigo_cargo_base=None,
            titular_cargo_base="",
        )

        queryset = AtoAdministrativo.objects.filter(
            tipo=AtoAdministrativo.Tipo.DESIGNACAO
        )

        resultado = DesignacaoService.get_cargos_pareados(
            queryset,
            "designacao_detalhe__indicado_codigo_cargo_base",
            "designacao_detalhe__indicado_cargo_base",
            "designacao_detalhe__titular_codigo_cargo_base",
            "designacao_detalhe__titular_cargo_base",
        )

        assert resultado == []

    def test_create_designacao(self):
        """Verifica create designação."""
        designacao = criar_ato_designacao()
        assert (
            designacao.status_publicacao
            == AtoAdministrativo.StatusPublicacao.NAO_PUBLICADO
        )

    def test_atualizar_campos_do_ato(self):
        """Verifica atualização de campos pertencentes ao ato."""
        designacao = criar_ato_designacao(numero_portaria="111")

        atualizado = DesignacaoService.atualizar(
            designacao, {"numero_portaria": "999"}
        )

        atualizado.refresh_from_db()
        assert atualizado.numero_portaria == "999"

    def test_atualizar_campos_do_detalhe(self):
        """Verifica atualização de campos pertencentes ao detalhe."""
        designacao = criar_ato_designacao(indicado_nome_civil="Antigo")

        atualizado = DesignacaoService.atualizar(
            designacao, {"indicado_nome_civil": "Novo Nome"}
        )

        atualizado.designacao_detalhe.refresh_from_db()
        assert atualizado.designacao_detalhe.indicado_nome_civil == "Novo Nome"

    def test_atualizar_campos_do_ato_e_do_detalhe(self):
        """Verifica atualização simultânea de campos do ato e do detalhe."""
        designacao = criar_ato_designacao(
            numero_portaria="111", indicado_nome_civil="Antigo"
        )

        atualizado = DesignacaoService.atualizar(
            designacao,
            {"numero_portaria": "222", "indicado_nome_civil": "Novo Nome"},
        )

        atualizado.refresh_from_db()
        atualizado.designacao_detalhe.refresh_from_db()
        assert atualizado.numero_portaria == "222"
        assert atualizado.designacao_detalhe.indicado_nome_civil == "Novo Nome"

    def test_get_cargos_pareados_remove_duplicados(self):
        """Verifica get cargos pareados remove duplicados."""
        criar_ato_designacao(
            indicado_codigo_cargo_base=1,
            indicado_cargo_base="Professor",
            titular_codigo_cargo_base=1,
            titular_cargo_base="Professor",
        )

        queryset = AtoAdministrativo.objects.filter(
            tipo=AtoAdministrativo.Tipo.DESIGNACAO
        )

        resultado = DesignacaoService.get_cargos_pareados(
            queryset,
            "designacao_detalhe__indicado_codigo_cargo_base",
            "designacao_detalhe__indicado_cargo_base",
            "designacao_detalhe__titular_codigo_cargo_base",
            "designacao_detalhe__titular_cargo_base",
        )

        assert resultado == [{"codigoCargo": 1, "nomeCargo": "Professor"}]
