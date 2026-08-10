"""Testes para os serializadores de CargoBase."""

import pytest

from apps.gestao.__tests__.factories import criar_cargo_base
from apps.gestao.api.serializers.cargo_base_serializer import (
    CargoBaseReadSerializer,
    CargoBaseUpdateSerializer,
    CargoBaseWriteSerializer,
)
from apps.gestao.models.cargo_base import CargoBase


@pytest.mark.django_db
def test_read_serializer_expoe_todos_os_campos():
    """Verifica que o serializer de leitura expõe os campos esperados."""
    cargo = criar_cargo_base()

    data = CargoBaseReadSerializer(cargo).data

    assert data["codigo_cargo"] == cargo.codigo_cargo
    assert data["descricao_completa"] == cargo.descricao_completa
    assert data["descricao_resumida"] == cargo.descricao_resumida
    assert data["grupamento"] == cargo.grupamento
    assert data["situacao_funcional"] == cargo.situacao_funcional
    assert data["status"] == cargo.status
    assert data["utilizado_para_funcoes"] == cargo.utilizado_para_funcoes
    assert (
        data["utilizado_para_designacoes"] == cargo.utilizado_para_designacoes
    )
    assert data["utilizado_para_ste"] == cargo.utilizado_para_ste
    assert data["utilizado_para_permutas"] == cargo.utilizado_para_permutas
    assert data["cargo_base_ficticio"] == cargo.cargo_base_ficticio
    assert "criado_em" in data


@pytest.mark.django_db
def test_read_serializer_expoe_displays_legiveis():
    """Verifica que o serializer de leitura expõe os labels legíveis."""
    cargo = criar_cargo_base(
        grupamento=CargoBase.Grupamento.GESTORES_EDUCACAO,
        situacao_funcional=CargoBase.SituacaoFuncional.EFETIVO,
        status=CargoBase.Status.ATIVO,
    )

    data = CargoBaseReadSerializer(cargo).data

    assert data["grupamento_display"] == "Gestores - educação"
    assert data["situacao_funcional_display"] == "Efetivo"
    assert data["status_display"] == "Ativo"


@pytest.mark.django_db
def test_write_serializer_valido_cria_cargo_base():
    """Verifica que o serializer de escrita valida e cria um cargo base."""
    payload = {
        "codigo_cargo": "3085",
        "descricao_completa": "ASSISTENTE DE DIRETOR DE ESCOLA",
        "descricao_resumida": "Assistente de Diretor",
        "grupamento": CargoBase.Grupamento.GESTORES_EDUCACAO,
        "situacao_funcional": CargoBase.SituacaoFuncional.EFETIVO,
    }

    serializer = CargoBaseWriteSerializer(data=payload)

    assert serializer.is_valid(), serializer.errors
    cargo = serializer.save()
    assert cargo.status == CargoBase.Status.ATIVO


@pytest.mark.django_db
def test_write_serializer_rejeita_codigo_cargo_duplicado():
    """Verifica que o serializer rejeita código de cargo já cadastrado."""
    criar_cargo_base(codigo_cargo="3360")

    payload = {
        "codigo_cargo": "3360",
        "descricao_completa": "DIRETOR DE ESCOLA",
        "descricao_resumida": "Diretor",
        "grupamento": CargoBase.Grupamento.GESTORES_EDUCACAO,
        "situacao_funcional": CargoBase.SituacaoFuncional.EFETIVO,
    }

    serializer = CargoBaseWriteSerializer(data=payload)

    assert not serializer.is_valid()
    assert "codigo_cargo" in serializer.errors


@pytest.mark.django_db
def test_write_serializer_rejeita_grupamento_invalido():
    """Verifica que o serializer rejeita valores fora das choices."""
    payload = {
        "codigo_cargo": "9999",
        "descricao_completa": "CARGO QUALQUER",
        "descricao_resumida": "Cargo Qualquer",
        "grupamento": "INVALIDO",
        "situacao_funcional": CargoBase.SituacaoFuncional.EFETIVO,
    }

    serializer = CargoBaseWriteSerializer(data=payload)

    assert not serializer.is_valid()
    assert "grupamento" in serializer.errors


@pytest.mark.django_db
def test_update_serializer_altera_campos_editaveis():
    """Verifica que o serializer de atualização altera os campos permitidos."""
    cargo = criar_cargo_base(
        descricao_resumida="Diretor de Escola",
        utilizado_para_permutas=False,
    )

    payload = {
        "descricao_resumida": "Diretor de Escola Municipal",
        "utilizado_para_permutas": True,
    }

    serializer = CargoBaseUpdateSerializer(cargo, data=payload, partial=True)

    assert serializer.is_valid(), serializer.errors
    cargo_atualizado = serializer.save()
    assert cargo_atualizado.descricao_resumida == "Diretor de Escola Municipal"
    assert cargo_atualizado.utilizado_para_permutas is True


@pytest.mark.django_db
def test_update_serializer_nao_expoe_codigo_cargo_e_descricao_completa():
    """Verifica que campos vindos do EOL não são editáveis via atualização."""
    cargo = criar_cargo_base(
        codigo_cargo="3360", descricao_completa="DIRETOR DE ESCOLA MUNICIPAL"
    )

    payload = {
        "codigo_cargo": "9999",
        "descricao_completa": "OUTRO CARGO QUALQUER",
    }

    serializer = CargoBaseUpdateSerializer(cargo, data=payload, partial=True)

    assert serializer.is_valid(), serializer.errors
    cargo_atualizado = serializer.save()
    assert cargo_atualizado.codigo_cargo == "3360"
    assert cargo_atualizado.descricao_completa == "DIRETOR DE ESCOLA MUNICIPAL"
