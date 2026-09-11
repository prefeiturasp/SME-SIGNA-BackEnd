"""Testes para o CargoBaseService."""

import pytest

from apps.gestao.__tests__.factories import criar_cargo_base
from apps.gestao.models.cargo_base import CargoBase
from apps.gestao.services.cargo_base_service import CargoBaseService


@pytest.mark.django_db
def test_listar_retorna_todos_os_cargos_cadastrados():
    """Verifica que listar retorna todos os cargos base cadastrados."""
    criar_cargo_base(codigo_cargo="3360")
    criar_cargo_base(codigo_cargo="3379")

    resultado = CargoBaseService.listar()

    assert resultado.count() == 2


@pytest.mark.django_db
def test_criar_cria_cargo_base_com_os_dados_informados():
    """Verifica que criar persiste um cargo base com os dados informados."""
    dados = {
        "codigo_cargo": "3352",
        "descricao_completa": "SUPERVISOR ESCOLAR",
        "descricao_resumida": "Supervisor Escolar",
        "grupamento": CargoBase.Grupamento.GESTORES_EDUCACAO,
        "situacao_funcional": CargoBase.SituacaoFuncional.EFETIVO,
        "status": CargoBase.Status.ATIVO,
    }

    cargo = CargoBaseService.criar(dados)

    assert cargo.pk is not None
    assert CargoBase.objects.filter(codigo_cargo="3352").exists()
