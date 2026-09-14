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
    assert data["tipo_ato_pai"] == modelo.tipo_ato_pai
    assert data["status"] == modelo.status
    assert data["nome_modelo"] == modelo.nome_modelo
    assert data["tipo_cargo"] == modelo.tipo_cargo
    assert data["variaveis"] == modelo.variaveis
    assert data["observacoes"] == modelo.observacoes
    assert data["texto_portaria"] == modelo.texto_portaria
    assert "criado_em" in data
    assert "atualizado_em" in data
    assert "tipo_de_ato" in data


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
def test_read_serializer_expoe_tipo_ato_pai_de_apostila():
    """Verifica que o serializer de leitura expõe o tipo do ato pai."""
    modelo = criar_modelo_portaria(
        nome_modelo="Apostila de cessação",
        tipo_portaria=AtoAdministrativo.Tipo.APOSTILA,
        tipo_ato_pai=AtoAdministrativo.Tipo.CESSACAO,
    )

    data = ModeloPortariaReadSerializer(modelo).data

    assert data["tipo_ato_pai"] == AtoAdministrativo.Tipo.CESSACAO
    assert data["tipo_ato_pai_display"] == "Cessação"


@pytest.mark.django_db
def test_read_serializer_expoe_tipo_de_ato_concatenado_quando_ha_pai():
    """Verifica a concatenação de tipo_portaria com tipo_ato_pai."""
    modelo = criar_modelo_portaria(
        nome_modelo="Apostila de cessação",
        tipo_portaria=AtoAdministrativo.Tipo.APOSTILA,
        tipo_ato_pai=AtoAdministrativo.Tipo.CESSACAO,
    )

    data = ModeloPortariaReadSerializer(modelo).data

    assert data["tipo_de_ato"] == "Apostila de Cessação"


@pytest.mark.django_db
def test_read_serializer_expoe_tipo_de_ato_sem_concatenar_quando_nao_ha_pai():
    """Verifica que tipo_de_ato não concatena quando não há ato pai."""
    modelo = criar_modelo_portaria(
        tipo_portaria=AtoAdministrativo.Tipo.DESIGNACAO,
        tipo_ato_pai="",
    )

    data = ModeloPortariaReadSerializer(modelo).data

    assert data["tipo_de_ato"] == "Designação"


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


@pytest.mark.django_db
def test_write_serializer_valido_cria_apostila_com_tipo_ato_pai():
    """Verifica que apostila é criada com tipo_ato_pai compatível."""
    payload = {
        "tipo_portaria": AtoAdministrativo.Tipo.APOSTILA,
        "tipo_ato_pai": AtoAdministrativo.Tipo.CESSACAO,
        "nome_modelo": "Apostila de cessação",
        "tipo_cargo": ModeloPortaria.TipoCargo.CARGO_VAGO,
        "texto_portaria": "Texto qualquer",
    }

    serializer = ModeloPortariaWriteSerializer(data=payload)

    assert serializer.is_valid(), serializer.errors
    modelo = serializer.save()
    assert modelo.tipo_ato_pai == AtoAdministrativo.Tipo.CESSACAO


@pytest.mark.django_db
def test_write_serializer_rejeita_tipo_ato_pai_ausente_para_apostila():
    """Verifica que apostila sem tipo_ato_pai é rejeitada."""
    payload = {
        "tipo_portaria": AtoAdministrativo.Tipo.APOSTILA,
        "nome_modelo": "Apostila sem pai",
        "tipo_cargo": ModeloPortaria.TipoCargo.CARGO_VAGO,
        "texto_portaria": "Texto qualquer",
    }

    serializer = ModeloPortariaWriteSerializer(data=payload)

    assert not serializer.is_valid()
    assert "tipo_ato_pai" in serializer.errors


@pytest.mark.django_db
def test_write_serializer_rejeita_tipo_ato_pai_invalido_para_apostila():
    """Verifica que apostila só aceita DESIGNACAO/CESSACAO como ato pai."""
    payload = {
        "tipo_portaria": AtoAdministrativo.Tipo.APOSTILA,
        "tipo_ato_pai": AtoAdministrativo.Tipo.INSUBSISTENCIA,
        "nome_modelo": "Apostila inválida",
        "tipo_cargo": ModeloPortaria.TipoCargo.CARGO_VAGO,
        "texto_portaria": "Texto qualquer",
    }

    serializer = ModeloPortariaWriteSerializer(data=payload)

    assert not serializer.is_valid()
    assert "tipo_ato_pai" in serializer.errors


@pytest.mark.django_db
def test_write_serializer_rejeita_tipo_ato_pai_para_designacao():
    """Verifica que designação não aceita tipo_ato_pai."""
    payload = {
        "tipo_portaria": AtoAdministrativo.Tipo.DESIGNACAO,
        "tipo_ato_pai": AtoAdministrativo.Tipo.CESSACAO,
        "nome_modelo": "Designação com pai indevido",
        "tipo_cargo": ModeloPortaria.TipoCargo.CARGO_VAGO,
        "texto_portaria": "Texto qualquer",
    }

    serializer = ModeloPortariaWriteSerializer(data=payload)

    assert not serializer.is_valid()
    assert "tipo_ato_pai" in serializer.errors


@pytest.mark.django_db
def test_write_serializer_valido_cria_insubsistencia_para_cada_tipo_pai():
    """Verifica que insubsistência aceita qualquer um dos 4 tipos pai."""
    for tipo_pai in [
        AtoAdministrativo.Tipo.DESIGNACAO,
        AtoAdministrativo.Tipo.CESSACAO,
        AtoAdministrativo.Tipo.APOSTILA,
        AtoAdministrativo.Tipo.INSUBSISTENCIA,
    ]:
        payload = {
            "tipo_portaria": AtoAdministrativo.Tipo.INSUBSISTENCIA,
            "tipo_ato_pai": tipo_pai,
            "nome_modelo": f"Insubsistência de {tipo_pai}",
            "tipo_cargo": ModeloPortaria.TipoCargo.CARGO_VAGO,
            "texto_portaria": "Texto qualquer",
        }

        serializer = ModeloPortariaWriteSerializer(data=payload)

        assert serializer.is_valid(), serializer.errors
