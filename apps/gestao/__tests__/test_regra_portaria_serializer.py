"""Testes para os serializadores de RegraPortaria."""

import pytest

from apps.gestao.__tests__.factories import criar_regra_portaria
from apps.gestao.api.serializers.regra_portaria_serializer import (
    RegraPortariaReadSerializer,
    RegraPortariaUpdateSerializer,
    RegraPortariaWriteSerializer,
)
from apps.gestao.models.regra_portaria import RegraPortaria


@pytest.mark.django_db
def test_read_serializer_expoe_todos_os_campos():
    """Verifica que o serializer de leitura expõe os campos esperados."""
    regra = criar_regra_portaria()

    data = RegraPortariaReadSerializer(regra).data

    assert data["descricao_resumida_cargo"] == regra.descricao_resumida_cargo
    assert data["descricao_completa_cargo"] == regra.descricao_completa_cargo
    assert data["codigo_cargo_eol"] == regra.codigo_cargo_eol
    assert data["tipo_modulo"] == regra.tipo_modulo
    assert data["status"] == regra.status
    assert data["texto_publicacao"] == regra.texto_publicacao
    assert data["emitente"] == regra.emitente
    assert data["normas"] == regra.normas
    assert data["observacoes"] == regra.observacoes
    assert data["utilizar_numero_sei"] == regra.utilizar_numero_sei
    assert "criado_em" in data
    assert "atualizado_em" in data


@pytest.mark.django_db
def test_read_serializer_expoe_displays_legiveis():
    """Verifica que o serializer de leitura expõe os labels legíveis."""
    regra = criar_regra_portaria(
        tipo_modulo=RegraPortaria.TipoModulo.TURMAS,
        status=RegraPortaria.Status.ATIVO,
        emitente=RegraPortaria.Emitente.SECRETARIO_MUNICIPAL_EDUCACAO,
    )

    data = RegraPortariaReadSerializer(regra).data

    assert data["tipo_modulo_display"] == "Turmas"
    assert data["status_display"] == "Ativo"
    assert data["emitente_display"] == "Secretário municipal de educação"


@pytest.mark.django_db
def test_write_serializer_valido_cria_regra_portaria():
    """Verifica que o serializer de escrita valida e cria uma regra."""
    payload = {
        "descricao_resumida_cargo": "Diretor",
        "descricao_completa_cargo": "Diretor de escola",
        "codigo_cargo_eol": "3360",
        "tipo_modulo": RegraPortaria.TipoModulo.TURMAS,
        "texto_publicacao": "Texto qualquer",
        "emitente": RegraPortaria.Emitente.SECRETARIO_MUNICIPAL_EDUCACAO,
    }

    serializer = RegraPortariaWriteSerializer(data=payload)

    assert serializer.is_valid(), serializer.errors
    regra = serializer.save()
    assert regra.status == RegraPortaria.Status.ATIVO
    assert regra.utilizar_numero_sei is False


@pytest.mark.django_db
def test_write_serializer_rejeita_tipo_modulo_invalido():
    """Verifica que o serializer rejeita valores fora das choices."""
    payload = {
        "descricao_resumida_cargo": "Diretor",
        "descricao_completa_cargo": "Diretor de escola",
        "codigo_cargo_eol": "3360",
        "tipo_modulo": "INVALIDO",
        "texto_publicacao": "Texto qualquer",
        "emitente": RegraPortaria.Emitente.SECRETARIO_MUNICIPAL_EDUCACAO,
    }

    serializer = RegraPortariaWriteSerializer(data=payload)

    assert not serializer.is_valid()
    assert "tipo_modulo" in serializer.errors


@pytest.mark.django_db
def test_write_serializer_rejeita_codigo_cargo_eol_duplicado():
    """Verifica que o serializer rejeita código EOL já cadastrado."""
    criar_regra_portaria(codigo_cargo_eol="3360")

    payload = {
        "descricao_resumida_cargo": "Diretor",
        "descricao_completa_cargo": "Diretor de escola",
        "codigo_cargo_eol": "3360",
        "tipo_modulo": RegraPortaria.TipoModulo.TURMAS,
        "texto_publicacao": "Texto qualquer",
        "emitente": RegraPortaria.Emitente.SECRETARIO_MUNICIPAL_EDUCACAO,
    }

    serializer = RegraPortariaWriteSerializer(data=payload)

    assert not serializer.is_valid()
    assert "codigo_cargo_eol" in serializer.errors


@pytest.mark.django_db
def test_update_serializer_altera_campos_informados():
    """Verifica que o serializer de atualização altera os campos."""
    regra = criar_regra_portaria(descricao_resumida_cargo="Diretor")

    serializer = RegraPortariaUpdateSerializer(
        regra,
        data={"descricao_resumida_cargo": "Diretor de Escola Municipal"},
        partial=True,
    )

    assert serializer.is_valid(), serializer.errors
    regra_atualizada = serializer.save()
    assert regra_atualizada.descricao_resumida_cargo == (
        "Diretor de Escola Municipal"
    )
