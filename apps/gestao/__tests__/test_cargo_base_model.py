"""Testes para o model CargoBase."""

import pytest
from django.db import IntegrityError

from apps.gestao.__tests__.factories import criar_cargo_base
from apps.gestao.models.cargo_base import CargoBase


@pytest.mark.django_db
def test_str_retorna_codigo_e_descricao_resumida():
    """Verifica a representação textual do cargo base."""
    cargo = criar_cargo_base(
        codigo_cargo="3379", descricao_resumida="Coordenador Pedagógico"
    )

    assert str(cargo) == "3379 - Coordenador Pedagógico"


@pytest.mark.django_db
def test_status_default_e_ativo():
    """Verifica que o status padrão de um cargo base é ATIVO."""
    cargo = CargoBase.objects.create(
        codigo_cargo="3182",
        descricao_completa="SECRETARIO DE ESCOLA",
        descricao_resumida="Secretário de Escola",
        grupamento=CargoBase.Grupamento.APOIO_EDUCACAO,
        situacao_funcional=CargoBase.SituacaoFuncional.COMISSIONADO,
    )

    assert cargo.status == CargoBase.Status.ATIVO


@pytest.mark.django_db
def test_codigo_cargo_deve_ser_unico():
    """Verifica que não é possível cadastrar dois cargos com o mesmo código."""
    criar_cargo_base(codigo_cargo="3085")

    with pytest.raises(IntegrityError):
        criar_cargo_base(codigo_cargo="3085")
