"""Testes para serviço de designação."""

import pytest

from apps.designacao.__tests__.factories import criar_ato_designacao
from apps.designacao.models.ato_administrativo import AtoAdministrativo
from apps.designacao.services.designacao_service import DesignacaoService


@pytest.mark.django_db
class TestDesignacaoService:
    """Testes para designacao service."""

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
