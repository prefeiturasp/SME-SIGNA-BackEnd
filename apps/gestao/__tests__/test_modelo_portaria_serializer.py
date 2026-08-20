"""Testes para os serializadores de ModeloPortaria."""

import pytest

from apps.designacao.models.ato_administrativo import AtoAdministrativo
from apps.gestao.__tests__.factories import criar_modelo_portaria
from apps.gestao.api.serializers.modelo_portaria_serializer import (
    ModeloPortariaReadSerializer,
    ModeloPortariaWriteSerializer,
)
from apps.gestao.models.modelo_portaria import ModeloPortaria


@pytest.mark.django_db
def test_read_serializer_expoe_todos_os_campos():
    """Verifica que o serializer de leitura expõe os campos esperados."""
    modelo = criar_modelo_portaria()

    data = ModeloPortariaReadSerializer(modelo).data

    assert data["tipo_portaria"] == modelo.tipo_portaria
    assert data["status"] == modelo.status
    assert data["nome_modelo"] == modelo.nome_modelo
    assert data["tipo_cargo"] == modelo.tipo_cargo
    assert data["variaveis"] == modelo.variaveis
    assert data["observacoes"] == modelo.observacoes
    assert data["texto_portaria"] == modelo.texto_portaria
    assert "criado_em" in data
    assert "atualizado_em" in data


@pytest.mark.django_db
def test_read_serializer_expoe_displays_legiveis():
    """Verifica que o serializer de leitura expõe os labels legíveis."""
    modelo = criar_modelo_portaria(
        tipo_portaria=AtoAdministrativo.Tipo.DESIGNACAO,
        status=ModeloPortaria.Status.ATIVO,
        tipo_cargo=ModeloPortaria.TipoCargo.CARGO_VAGO,
    )

    data = ModeloPortariaReadSerializer(modelo).data

    assert data["tipo_portaria_display"] == "Designação"
    assert data["status_display"] == "Ativo"
    assert data["tipo_cargo_display"] == "Cargo vago"


@pytest.mark.django_db
def test_write_serializer_valido_cria_modelo_portaria():
    """Verifica que o serializer de escrita valida e cria um modelo."""
    payload = {
        "tipo_portaria": AtoAdministrativo.Tipo.DESIGNACAO,
        "nome_modelo": "Designação diretor de escola",
        "tipo_cargo": ModeloPortaria.TipoCargo.CARGO_VAGO,
        "variaveis": [
            ModeloPortaria.Variavel.NOME_SERVIDOR,
            ModeloPortaria.Variavel.NUMERO_RF,
        ],
        "texto_portaria": "O Secretário Municipal de Educação designa...",
    }

    serializer = ModeloPortariaWriteSerializer(data=payload)

    assert serializer.is_valid(), serializer.errors
    modelo = serializer.save()
    assert modelo.status == ModeloPortaria.Status.ATIVO


@pytest.mark.django_db
def test_write_serializer_rejeita_tipo_portaria_invalido():
    """Verifica que o serializer rejeita valores fora das choices."""
    payload = {
        "tipo_portaria": "INVALIDO",
        "nome_modelo": "Designação diretor de escola",
        "tipo_cargo": ModeloPortaria.TipoCargo.CARGO_VAGO,
        "texto_portaria": "Texto qualquer",
    }

    serializer = ModeloPortariaWriteSerializer(data=payload)

    assert not serializer.is_valid()
    assert "tipo_portaria" in serializer.errors


@pytest.mark.django_db
def test_write_serializer_rejeita_variavel_invalida():
    """Verifica que o serializer rejeita variáveis fora das choices."""
    payload = {
        "tipo_portaria": AtoAdministrativo.Tipo.DESIGNACAO,
        "nome_modelo": "Designação diretor de escola",
        "tipo_cargo": ModeloPortaria.TipoCargo.CARGO_VAGO,
        "variaveis": ["INEXISTENTE"],
        "texto_portaria": "Texto qualquer",
    }

    serializer = ModeloPortariaWriteSerializer(data=payload)

    assert not serializer.is_valid()
    assert "variaveis" in serializer.errors
