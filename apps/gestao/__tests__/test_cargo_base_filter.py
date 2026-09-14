"""Testes para o CargoBaseFilter."""

import pytest

from apps.gestao.__tests__.factories import criar_cargo_base
from apps.gestao.api.filters.cargo_base_filter import CargoBaseFilter
from apps.gestao.models.cargo_base import CargoBase


@pytest.mark.django_db
def test_filtra_por_grupamento():
    """Verifica que o filtro por grupamento retorna só os cargos do grupo."""
    criar_cargo_base(
        codigo_cargo="3360", grupamento=CargoBase.Grupamento.GESTORES_EDUCACAO
    )
    criar_cargo_base(
        codigo_cargo="3379", grupamento=CargoBase.Grupamento.DOCENTES
    )

    resultado = CargoBaseFilter(
        {"grupamento": CargoBase.Grupamento.DOCENTES},
        queryset=CargoBase.objects.all(),
    ).qs

    assert resultado.count() == 1
    assert resultado.first().codigo_cargo == "3379"


@pytest.mark.django_db
def test_filtra_por_descricao_resumida_parcial():
    """Verifica que o filtro por descrição resumida faz busca parcial."""
    criar_cargo_base(
        codigo_cargo="3360", descricao_resumida="Diretor de Escola"
    )
    criar_cargo_base(
        codigo_cargo="3182", descricao_resumida="Secretário de Escola"
    )

    resultado = CargoBaseFilter(
        {"descricao_resumida": "diretor"},
        queryset=CargoBase.objects.all(),
    ).qs

    assert resultado.count() == 1
    assert resultado.first().codigo_cargo == "3360"


@pytest.mark.django_db
def test_filtra_por_descricao_completa_parcial():
    """Verifica que o filtro por descrição completa faz busca parcial."""
    criar_cargo_base(
        codigo_cargo="3360", descricao_completa="DIRETOR DE ESCOLA MUNICIPAL"
    )
    criar_cargo_base(
        codigo_cargo="3182", descricao_completa="SECRETARIO DE ESCOLA"
    )

    resultado = CargoBaseFilter(
        {"descricao_completa": "secretario"},
        queryset=CargoBase.objects.all(),
    ).qs

    assert resultado.count() == 1
    assert resultado.first().codigo_cargo == "3182"


@pytest.mark.django_db
def test_filtra_por_situacao_funcional():
    """Verifica que o filtro por situação funcional retorna os compatíveis."""
    criar_cargo_base(
        codigo_cargo="3360",
        situacao_funcional=CargoBase.SituacaoFuncional.EFETIVO,
    )
    criar_cargo_base(
        codigo_cargo="3182",
        situacao_funcional=CargoBase.SituacaoFuncional.CONTRATADO,
    )

    resultado = CargoBaseFilter(
        {"situacao_funcional": CargoBase.SituacaoFuncional.CONTRATADO},
        queryset=CargoBase.objects.all(),
    ).qs

    assert resultado.count() == 1
    assert resultado.first().codigo_cargo == "3182"


@pytest.mark.django_db
def test_filtra_por_status():
    """Verifica que o filtro por status retorna os compatíveis."""
    criar_cargo_base(codigo_cargo="3360", status=CargoBase.Status.ATIVO)
    criar_cargo_base(codigo_cargo="3182", status=CargoBase.Status.EXTINTO)

    resultado = CargoBaseFilter(
        {"status": CargoBase.Status.EXTINTO},
        queryset=CargoBase.objects.all(),
    ).qs

    assert resultado.count() == 1
    assert resultado.first().codigo_cargo == "3182"


@pytest.mark.django_db
def test_combina_multiplos_filtros():
    """Verifica que múltiplos filtros preenchidos são combinados (E lógico)."""
    criar_cargo_base(
        codigo_cargo="3360",
        grupamento=CargoBase.Grupamento.GESTORES_EDUCACAO,
        status=CargoBase.Status.ATIVO,
    )
    criar_cargo_base(
        codigo_cargo="3379",
        grupamento=CargoBase.Grupamento.GESTORES_EDUCACAO,
        status=CargoBase.Status.INATIVO,
    )

    resultado = CargoBaseFilter(
        {
            "grupamento": CargoBase.Grupamento.GESTORES_EDUCACAO,
            "status": CargoBase.Status.ATIVO,
        },
        queryset=CargoBase.objects.all(),
    ).qs

    assert resultado.count() == 1
    assert resultado.first().codigo_cargo == "3360"


@pytest.mark.django_db
def test_sem_filtros_retorna_todos():
    """Verifica que a ausência de filtros retorna todos os cargos."""
    criar_cargo_base(codigo_cargo="3360")
    criar_cargo_base(codigo_cargo="3182")

    resultado = CargoBaseFilter({}, queryset=CargoBase.objects.all()).qs

    assert resultado.count() == 2
