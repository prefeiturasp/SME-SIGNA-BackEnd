"""Testes para o model RegraPortaria."""

import pytest
from django.db import IntegrityError

from apps.gestao.__tests__.factories import criar_regra_portaria
from apps.gestao.models.regra_portaria import RegraPortaria


@pytest.mark.django_db
def test_str_retorna_descricao_resumida_do_cargo():
    """Verifica a representação textual da regra de portaria."""
    regra = criar_regra_portaria(descricao_resumida_cargo="Diretor")

    assert str(regra) == "Diretor"


@pytest.mark.django_db
def test_status_default_e_ativo():
    """Verifica que o status padrão de uma regra de portaria é ATIVO."""
    regra = RegraPortaria.objects.create(
        descricao_resumida_cargo="Diretor",
        descricao_completa_cargo="Diretor de escola",
        codigo_cargo_eol="3360",
        tipo_modulo=RegraPortaria.TipoModulo.TURMAS,
        texto_publicacao="Texto qualquer",
        emitente=RegraPortaria.Emitente.SECRETARIO_MUNICIPAL_EDUCACAO,
    )

    assert regra.status == RegraPortaria.Status.ATIVO


@pytest.mark.django_db
def test_utilizar_numero_sei_default_e_falso():
    """Verifica que o campo utilizar_numero_sei é falso por padrão."""
    regra = RegraPortaria.objects.create(
        descricao_resumida_cargo="Diretor",
        descricao_completa_cargo="Diretor de escola",
        codigo_cargo_eol="3360",
        tipo_modulo=RegraPortaria.TipoModulo.TURMAS,
        texto_publicacao="Texto qualquer",
        emitente=RegraPortaria.Emitente.SECRETARIO_MUNICIPAL_EDUCACAO,
    )

    assert regra.utilizar_numero_sei is False


@pytest.mark.django_db
def test_codigo_cargo_eol_e_unico():
    """Verifica que o código do cargo no EOL é único."""
    criar_regra_portaria(codigo_cargo_eol="3360")

    with pytest.raises(IntegrityError):
        criar_regra_portaria(codigo_cargo_eol="3360")
