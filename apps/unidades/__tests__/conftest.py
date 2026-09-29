"""Fixtures e constantes de teste para o módulo de unidades.

Este arquivo define constantes de teste e fixtures reutilizáveis para os
testes do pacote apps.unidades. Ele inclui dados de DRE, unidades,
respostas mockadas e helpers para criar requests DRF.
"""

from unittest.mock import Mock

import pytest
from rest_framework.request import Request
from rest_framework.test import APIRequestFactory

# ==================== CONSTANTES ====================

# Códigos de teste
CODIGO_DRE_BUTANTA = "108100"
CODIGO_DRE_CAMPO_LIMPO = "108200"
CODIGO_EOL_EMEF = "019456"
CODIGO_EOL_EMEI = "019457"

# Nomes de DRE
NOME_DRE_BUTANTA = "Diretoria Regional de Educação Butantã"
NOME_DRE_CAMPO_LIMPO = "Diretoria Regional de Educação Campo Limpo"
NOME_DRE_CENTRO = "DRE Centro"

# Siglas de DRE
SIGLA_DRE_BUTANTA = "DRE-BT"
SIGLA_DRE_CAMPO_LIMPO = "DRE-CL"
SIGLA_DRE_CENTRO = "DRE-CT"

# Nomes de unidades
NOME_EMEF = "EMEF - Escola Municipal de Ensino Fundamental"
NOME_EMEI = "EMEI - Escola Municipal de Educação Infantil"

# Tipos de unidade
TIPO_UE_EMEF = "EMEF"
TIPO_UE_EMEI = "EMEI"

# ==================== FIXTURES DE DADOS ====================


@pytest.fixture
def dados_dre_validos():
    """Fixture com dados válidos de DRE."""
    return {
        "codigo_dre": "001",
        "nome_dre": NOME_DRE_CENTRO,
        "sigla_dre": SIGLA_DRE_CENTRO,
    }


@pytest.fixture
def dados_unidade_completos():
    """Fixture com dados completos de uma unidade."""
    return {
        "codigo_eol": "123456",
        "nome_oficial": "Escola Municipal de Ensino Fundamental",
        "nome_nao_oficial": "EMEF Centro",
        "tipo_unidade_admin": TIPO_UE_EMEF,
        "tipo_ue": TIPO_UE_EMEF,
        "logradouro": "Rua das Flores",
        "numero": "100",
        "bairro": "Centro",
        "cep": 12345678,
        "distrito": "Centro",
        "sub_prefeitura": "Sé",
        "nome_dre": NOME_DRE_CENTRO,
        "email": "escola@exemplo.com",
        "telefone1": "11-1234-5678",
        "telefone2": "11-8765-4321",
        "ano_construcao": 1990,
        "propriedade": "Municipal",
        "capacidade_vagas_matutino": 200,
        "capacidade_vagas_vespertino": 200,
        "capacidade_vagas_noturno": 100,
        "capacidade_vagas_intermediario": 50,
        "capacidade_vagas_integral": 150,
        "capacidade_vagas_total": 700,
        "organizacao_parceira": False,
        "quantidade_funcionarios": 50,
        "status": "Ativa",
    }


@pytest.fixture
def dados_unidade_completos_camelcase():
    """Fixture com dados completos em camelCase."""
    return {
        "codigoEol": "123456",
        "nomeOficial": "Escola Municipal de Ensino Fundamental",
        "nomeNaoOficial": "EMEF Centro",
        "tipoUnidadeAdmin": TIPO_UE_EMEF,
        "tipoUE": TIPO_UE_EMEF,
        "logradouro": "Rua das Flores",
        "numero": "100",
        "bairro": "Centro",
        "cep": 12345678,
        "distrito": "Centro",
        "subPrefeitura": "Sé",
        "nomeDre": NOME_DRE_CENTRO,
        "email": "escola@exemplo.com",
        "telefone1": "11-1234-5678",
        "telefone2": "11-8765-4321",
        "anoConstrucao": 1990,
        "propriedade": "Municipal",
        "capacidadeVagasMatutino": 200,
        "capacidadeVagasVespertino": 200,
        "capacidadeVagasNoturno": 100,
        "capacidadeVagasIntermediario": 50,
        "capacidadeVagasIntegral": 150,
        "capacidadeVagasTotal": 700,
        "organizacaoParceira": False,
        "quantidadeDeFuncionarios": 50,
        "status": "Ativa",
    }


@pytest.fixture
def dados_unidade_minimos():
    """Fixture com dados mínimos obrigatórios."""
    return {
        "codigo_eol": "123456",
        "nome_oficial": "Escola Municipal",
        "tipo_unidade_admin": TIPO_UE_EMEF,
        "tipo_ue": TIPO_UE_EMEF,
        "nome_dre": NOME_DRE_CENTRO,
    }


@pytest.fixture
def dados_unidade_minimos_camelcase():
    """Fixture com dados mínimos em camelCase."""
    return {
        "codigoEol": "123456",
        "nomeOficial": "Escola Municipal",
        "tipoUnidadeAdmin": TIPO_UE_EMEF,
        "tipoUE": TIPO_UE_EMEF,
        "nomeDre": NOME_DRE_CENTRO,
    }


# ==================== FIXTURES DE MOCK RESPONSES ====================


@pytest.fixture
def mock_dres_response():
    """Fixture com resposta mockada de DREs da API."""
    return [
        {
            "codigoDRE": CODIGO_DRE_BUTANTA,
            "nomeDRE": NOME_DRE_BUTANTA,
            "siglaDRE": SIGLA_DRE_BUTANTA,
        },
        {
            "codigoDRE": CODIGO_DRE_CAMPO_LIMPO,
            "nomeDRE": NOME_DRE_CAMPO_LIMPO,
            "siglaDRE": SIGLA_DRE_CAMPO_LIMPO,
        },
    ]


@pytest.fixture
def mock_unidades_response():
    """Fixture com resposta mockada de unidades da API."""
    return [
        {
            "codigoEol": CODIGO_EOL_EMEF,
            "nomeOficial": NOME_EMEF,
            "tipoUE": TIPO_UE_EMEF,
            "nomeDRE": NOME_DRE_BUTANTA,
        },
        {
            "codigoEol": CODIGO_EOL_EMEI,
            "nomeOficial": NOME_EMEI,
            "tipoUE": TIPO_UE_EMEI,
            "nomeDRE": NOME_DRE_BUTANTA,
        },
    ]


# ==================== FIXTURES PARA VIEWSET ====================


@pytest.fixture
def api_factory():
    """Fixture para criar requests de teste do DRF."""
    return APIRequestFactory()


@pytest.fixture
def create_drf_request(api_factory):
    """Cria uma fixture que gera requests DRF válidas."""

    def _create_request(
        method="get",
        path="/api/unidades/",
        data=None,
        query_params=None,
    ):
        """Cria uma request DRF mockada para testes."""
        data = data or {}
        query_params = query_params or {}

        if method.lower() == "get":
            wsgi_request = api_factory.get(path, query_params)
        elif method.lower() == "post":
            wsgi_request = api_factory.post(
                path,
                data,
                format="json",
            )
        elif method.lower() == "put":
            wsgi_request = api_factory.put(
                path,
                data,
                format="json",
            )
        elif method.lower() == "patch":
            wsgi_request = api_factory.patch(
                path,
                data,
                format="json",
            )
        elif method.lower() == "delete":
            wsgi_request = api_factory.delete(path)
        else:
            raise ValueError(f"Método HTTP não suportado: {method}")

        return Request(wsgi_request)

    return _create_request


# ==================== FIXTURES DE MOCK HTTP ====================


@pytest.fixture
def mock_http_response_success():
    """Fixture para criar resposta HTTP mockada de sucesso."""

    def _create_response(data, status_code=200):
        """Cria um objeto de resposta HTTP mockado com sucesso."""
        mock_response = Mock()
        mock_response.status_code = status_code
        mock_response.json.return_value = data
        mock_response.text = str(data)
        return mock_response

    return _create_response


@pytest.fixture
def mock_http_response_error():
    """Fixture para criar resposta HTTP mockada de erro."""

    def _create_response(status_code, text="Error"):
        """Cria um objeto de resposta HTTP mockado com erro."""
        mock_response = Mock()
        mock_response.status_code = status_code
        mock_response.text = text
        mock_response.json.return_value = {}
        return mock_response

    return _create_response


# ==================== FIXTURES DE CONFIGURAÇÃO ====================


@pytest.fixture
def mock_env_config():
    """Fixture para mockar variáveis de ambiente."""

    def _config(
        url="https://api.test.com",
        token="test-token-123",
    ):
        """Retorna função mock para leitura de variáveis."""
        return lambda key, default="": {
            "SME_INTEGRACAO_URL": url,
            "SME_INTEGRACAO_TOKEN": token,
        }.get(key, default)

    return _config


# ==================== FIXTURES DE CÓDIGOS ====================


@pytest.fixture
def codigo_dre_valido():
    """Código de DRE válido para testes."""
    return CODIGO_DRE_BUTANTA


@pytest.fixture
def codigo_dre_invalido():
    """Código de DRE inválido para testes."""
    return "999999"


@pytest.fixture
def codigo_eol_valido():
    """Código EOL válido para testes."""
    return CODIGO_EOL_EMEF
