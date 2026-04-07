import pytest
from apps.designacao.models.designacao import Designacao
from apps.designacao.services.designacao_service import DesignacaoService
from apps.designacao.__tests__.factories import criar_designacao


@pytest.mark.django_db
class TestDesignacaoService:

    def test_get_cargos_pareados_sucesso(self):
        """
        Deve retornar cargos únicos, combinando indicado + titular,
        ordenados pelo nome.
        """

        criar_designacao(
            indicado_codigo_cargo_base=1,
            indicado_cargo_base="Professor",
            titular_codigo_cargo_base=2,
            titular_cargo_base="Diretor"
        )

        criar_designacao(
            indicado_codigo_cargo_base=3,
            indicado_cargo_base="Coordenador",
        )

        queryset = Designacao.objects.all()

        resultado = DesignacaoService.get_cargos_pareados(
            queryset,
            "indicado_codigo_cargo_base",
            "indicado_cargo_base",
            "titular_codigo_cargo_base",
            "titular_cargo_base",
        )

        assert resultado == [
            {"codigoCargo": 3, "nomeCargo": "Coordenador"},
            {"codigoCargo": 2, "nomeCargo": "Diretor"},
            {"codigoCargo": 1, "nomeCargo": "Professor"},
        ]

    def test_get_cargos_pareados_remove_invalidos(self):
        """
        Deve ignorar registros com nome vazio ou código nulo.
        """

        criar_designacao(
            indicado_codigo_cargo_base=None,
            indicado_cargo_base="",
            titular_codigo_cargo_base=None,
            titular_cargo_base=""
        )

        queryset = Designacao.objects.all()

        resultado = DesignacaoService.get_cargos_pareados(
            queryset,
            "indicado_codigo_cargo_base",
            "indicado_cargo_base",
            "titular_codigo_cargo_base",
            "titular_cargo_base",
        )

        assert resultado == []

    def test_get_cargos_pareados_remove_duplicados(self):
        """
        Deve remover duplicados automaticamente (UNION).
        """

        criar_designacao(
            indicado_codigo_cargo_base=1,
            indicado_cargo_base="Professor",
            titular_codigo_cargo_base=1,
            titular_cargo_base="Professor"
        )

        queryset = Designacao.objects.all()

        resultado = DesignacaoService.get_cargos_pareados(
            queryset,
            "indicado_codigo_cargo_base",
            "indicado_cargo_base",
            "titular_codigo_cargo_base",
            "titular_cargo_base",
        )

        assert resultado == [
            {"codigoCargo": 1, "nomeCargo": "Professor"},
        ]