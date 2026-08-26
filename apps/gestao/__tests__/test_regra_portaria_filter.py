"""Testes para o RegraPortariaFilter."""

import pytest

from apps.gestao.__tests__.factories import criar_regra_portaria
from apps.gestao.api.filters.regra_portaria_filter import RegraPortariaFilter
from apps.gestao.models.regra_portaria import RegraPortaria


@pytest.mark.django_db
def test_filtra_por_cargo_parcial():
    """Verifica que o filtro por cargo faz busca parcial no cargo."""
    criar_regra_portaria(
        codigo_cargo_eol="3360", descricao_resumida_cargo="Diretor"
    )
    criar_regra_portaria(
        codigo_cargo_eol="3182", descricao_resumida_cargo="Secretário"
    )

    resultado = RegraPortariaFilter(
        {"cargo": "diretor"},
        queryset=RegraPortaria.objects.all(),
    ).qs

    assert resultado.count() == 1
    assert resultado.first().codigo_cargo_eol == "3360"


@pytest.mark.django_db
def test_filtra_por_codigo_cargo_eol_parcial():
    """Verifica que o filtro por código EOL faz busca parcial."""
    criar_regra_portaria(codigo_cargo_eol="3360")
    criar_regra_portaria(codigo_cargo_eol="3182")

    resultado = RegraPortariaFilter(
        {"codigo_cargo_eol": "336"},
        queryset=RegraPortaria.objects.all(),
    ).qs

    assert resultado.count() == 1
    assert resultado.first().codigo_cargo_eol == "3360"


@pytest.mark.django_db
def test_filtra_por_tipo_modulo():
    """Verifica que o filtro por tipo de módulo retorna os compatíveis."""
    criar_regra_portaria(
        codigo_cargo_eol="3360",
        tipo_modulo=RegraPortaria.TipoModulo.TURMAS,
    )
    criar_regra_portaria(
        codigo_cargo_eol="3352",
        tipo_modulo=RegraPortaria.TipoModulo.ESPECIFICO_SUPERVISOR,
    )

    resultado = RegraPortariaFilter(
        {"tipo_modulo": RegraPortaria.TipoModulo.ESPECIFICO_SUPERVISOR},
        queryset=RegraPortaria.objects.all(),
    ).qs

    assert resultado.count() == 1
    assert resultado.first().codigo_cargo_eol == "3352"


@pytest.mark.django_db
def test_filtra_por_status():
    """Verifica que o filtro por status retorna os compatíveis."""
    criar_regra_portaria(
        codigo_cargo_eol="3360", status=RegraPortaria.Status.ATIVO
    )
    criar_regra_portaria(
        codigo_cargo_eol="3182", status=RegraPortaria.Status.INATIVO
    )

    resultado = RegraPortariaFilter(
        {"status": RegraPortaria.Status.INATIVO},
        queryset=RegraPortaria.objects.all(),
    ).qs

    assert resultado.count() == 1
    assert resultado.first().codigo_cargo_eol == "3182"


@pytest.mark.django_db
def test_combina_multiplos_filtros():
    """Verifica que múltiplos filtros preenchidos são combinados (E lógico)."""
    criar_regra_portaria(
        codigo_cargo_eol="3360",
        tipo_modulo=RegraPortaria.TipoModulo.TURMAS,
        status=RegraPortaria.Status.ATIVO,
    )
    criar_regra_portaria(
        codigo_cargo_eol="3379",
        tipo_modulo=RegraPortaria.TipoModulo.TURMAS,
        status=RegraPortaria.Status.INATIVO,
    )

    resultado = RegraPortariaFilter(
        {
            "tipo_modulo": RegraPortaria.TipoModulo.TURMAS,
            "status": RegraPortaria.Status.ATIVO,
        },
        queryset=RegraPortaria.objects.all(),
    ).qs

    assert resultado.count() == 1
    assert resultado.first().codigo_cargo_eol == "3360"


@pytest.mark.django_db
def test_sem_filtros_retorna_todos():
    """Verifica que a ausência de filtros retorna todas as regras."""
    criar_regra_portaria(codigo_cargo_eol="3360")
    criar_regra_portaria(codigo_cargo_eol="3182")

    resultado = RegraPortariaFilter(
        {}, queryset=RegraPortaria.objects.all()
    ).qs

    assert resultado.count() == 2
