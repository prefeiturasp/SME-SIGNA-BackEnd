"""Testes dos serviços de integração de unidades.

Este módulo contém testes de unidade para os serviços de integração
com o EOL, verificando fluxos de sucesso, validação de respostas e
propagação de erros.
"""

from unittest.mock import Mock, patch

import pytest
import requests

from apps.unidades.services.unidades_service import (
    BaseEOLService,
    DREIntegracaoService,
    EOLCommunicationError,
    EOLIntegrationError,
    EOLTimeoutError,
    EOLUnexpectedResponseError,
    UnidadeIntegracaoService,
)

# ================= BASE SERVICE =================


class TestBaseEOLService:
    """Testa o comportamento do serviço base de integração com EOL.

    Verifica tratamento de códigos de status HTTP, timeouts e lançamento
    de exceções específicas para erros de integração.
    """

    @patch("apps.unidades.services.unidades_service.requests.get")
    def test_get_sucesso_dict(self, mock_get):
        """Deve retornar dicionário quando resposta HTTP for válida."""
        mock_response = Mock(status_code=200)
        mock_response.json.return_value = {"ok": True}
        mock_get.return_value = mock_response

        result = BaseEOLService._get("url", "ctx")

        assert result == {"ok": True}

    @patch("apps.unidades.services.unidades_service.requests.get")
    def test_get_401(self, mock_get):
        """Deve lançar PermissionError para resposta HTTP 401."""
        mock_get.return_value = Mock(status_code=401)

        with pytest.raises(PermissionError):
            BaseEOLService._get("url", "ctx")

    @patch("apps.unidades.services.unidades_service.requests.get")
    def test_get_404(self, mock_get):
        """Deve lançar LookupError para resposta HTTP 404."""
        mock_get.return_value = Mock(status_code=404)

        with pytest.raises(LookupError):
            BaseEOLService._get("url", "ctx")

    @patch("apps.unidades.services.unidades_service.requests.get")
    def test_get_status_erro(self, mock_get):
        """Deve lançar erro de integração para status HTTP inválido."""
        mock_response = Mock(status_code=500, text="erro")
        mock_get.return_value = mock_response

        with pytest.raises(EOLIntegrationError):
            BaseEOLService._get("url", "ctx")

    @patch("apps.unidades.services.unidades_service.requests.get")
    def test_get_timeout(self, mock_get):
        """Deve lançar timeout quando requisição exceder o tempo limite."""
        mock_get.side_effect = requests.exceptions.Timeout()

        with pytest.raises(EOLTimeoutError):
            BaseEOLService._get("url", "ctx")

    @patch("apps.unidades.services.unidades_service.requests.get")
    def test_get_request_exception(self, mock_get):
        """Deve lançar erro de comunicação para falhas de request."""
        mock_get.side_effect = requests.exceptions.RequestException("erro")

        with pytest.raises(EOLCommunicationError):
            BaseEOLService._get("url", "ctx")


# ================= DRE =================


class TestDREIntegracaoService:
    """Testa o serviço de integração de DREs.

    Valida a recuperação de DREs, a resposta esperada e a busca por código
    de DRE.
    """

    @patch("apps.unidades.services.unidades_service.env")
    @patch.object(BaseEOLService, "_get")
    def test_get_dres(
        self,
        mock_get,
        mock_env,
        mock_env_config,
        mock_dres_response,
    ):
        """Deve retornar lista de DREs com sucesso."""
        mock_env.side_effect = mock_env_config()
        mock_get.return_value = mock_dres_response

        result = DREIntegracaoService.get_dres()

        assert result == mock_dres_response

    @patch("apps.unidades.services.unidades_service.env")
    @patch.object(BaseEOLService, "_get")
    def test_get_dres_resposta_invalida(
        self,
        mock_get,
        mock_env,
        mock_env_config,
    ):
        """Deve lançar erro para resposta inválida de DREs."""
        mock_env.side_effect = mock_env_config()
        mock_get.return_value = {}

        with pytest.raises(EOLUnexpectedResponseError):
            DREIntegracaoService.get_dres()

    @patch.object(DREIntegracaoService, "get_dres")
    def test_get_dre_by_codigo_encontrada(
        self,
        mock_get_dres,
        mock_dres_response,
        codigo_dre_valido,
    ):
        """Deve retornar DRE encontrada pelo código."""
        mock_get_dres.return_value = mock_dres_response

        result = DREIntegracaoService.get_dre_by_codigo(
            codigo_dre_valido,
        )

        assert result["codigoDRE"] == codigo_dre_valido

    @patch.object(DREIntegracaoService, "get_dres")
    def test_get_dre_by_codigo_none(self, mock_get_dres):
        """Deve retornar None quando DRE não existir."""
        mock_get_dres.return_value = []

        assert DREIntegracaoService.get_dre_by_codigo("1") is None


# ================= UNIDADES =================


class TestUnidadeIntegracaoService:
    """Testa o serviço de integração de unidades.

    Abrange a recuperação de unidades por DRE, validação de parâmetros e
    tratamento de respostas inesperadas.
    """

    @patch("apps.unidades.services.unidades_service.env")
    @patch.object(BaseEOLService, "_get")
    def test_get_unidades(
        self,
        mock_get,
        mock_env,
        mock_env_config,
        mock_unidades_response,
        codigo_dre_valido,
    ):
        """Deve retornar unidades da DRE informada."""
        mock_env.side_effect = mock_env_config()
        mock_get.return_value = mock_unidades_response

        result = UnidadeIntegracaoService.get_unidades_by_dre(
            codigo_dre_valido,
        )

        assert result == mock_unidades_response

    @patch.object(BaseEOLService, "_get")
    def test_get_unidades_codigo_invalido(self, mock_get):
        """Deve lançar erro para código de DRE inválido."""
        with pytest.raises(ValueError):
            UnidadeIntegracaoService.get_unidades_by_dre("")

        mock_get.assert_not_called()

    @patch("apps.unidades.services.unidades_service.env")
    @patch.object(BaseEOLService, "_get")
    def test_get_unidades_resposta_invalida(
        self,
        mock_get,
        mock_env,
        mock_env_config,
        codigo_dre_valido,
    ):
        """Deve lançar erro para resposta inválida de unidades."""
        mock_env.side_effect = mock_env_config()
        mock_get.return_value = {}

        with pytest.raises(EOLUnexpectedResponseError):
            UnidadeIntegracaoService.get_unidades_by_dre(
                codigo_dre_valido,
            )

    @patch("apps.unidades.services.unidades_service.env")
    @patch.object(BaseEOLService, "_get")
    def test_get_escolas(
        self,
        mock_get,
        mock_env,
        mock_env_config,
        mock_unidades_response,
        codigo_dre_valido,
    ):
        """Deve retornar unidades filtradas por tipo."""
        mock_env.side_effect = mock_env_config()
        mock_get.return_value = mock_unidades_response

        result = UnidadeIntegracaoService.get_unidades_by_dre_com_tipo_unidade(
            codigo_dre_valido,
        )

        assert result == mock_unidades_response

    @patch("apps.unidades.services.unidades_service.env")
    @patch.object(BaseEOLService, "_get")
    def test_get_codigo_integracao(
        self,
        mock_get,
        mock_env,
        mock_env_config,
        mock_unidades_response,
        codigo_dre_valido,
    ):
        """Deve retornar códigos de integração das unidades."""
        mock_env.side_effect = mock_env_config()
        mock_get.return_value = mock_unidades_response

        result = (
            UnidadeIntegracaoService.get_unidades_codigo_integracao_by_dre(
                codigo_dre_valido,
            )
        )

        assert result == mock_unidades_response


# ================= SUPERVISAO =================


class TestUnidadeSupervisao:
    """Testa o lookup de unidade de supervisão por DRE.

    Verifica mapeamento de supervisão, respostas válidas e propagação de
    exceções específicas de integração.
    """

    @patch(
        "apps.unidades.services.unidades_service."
        "SUPERVISAO_ESCOLAR_DRES_MAP"
    )
    @patch.object(BaseEOLService, "_get")
    @patch("apps.unidades.services.unidades_service.env")
    def test_sucesso(
        self,
        mock_env,
        mock_get,
        mock_map,
        mock_env_config,
    ):
        """Deve retornar unidade de supervisão com sucesso."""
        mock_env.side_effect = mock_env_config()
        mock_map.get.return_value = "123"

        mock_get.return_value = {
            "codigo": 1,
            "nome": "Escola Teste",
            "codigoDRE": "10",
            "tipoUnidade": "CEU",
            "nomeDRE": "DRE Teste",
            "siglaDRE": "DT",
        }

        result = UnidadeIntegracaoService.get_unidade_supervisao_by_dre("10")

        assert result == {
            "codigoEscola": 1,
            "nomeEscola": "Escola Teste",
            "codigoDRE": "10",
            "tipoEscola": "CEU",
            "siglaTipoEscola": "UA",
            "nomeDRE": "DRE Teste",
            "siglaDRE": "DT",
            "codigoSubprefeitura": None,
            "nomeSubprefeitura": None,
        }

    def test_dre_codigo_invalido(self):
        """Deve lançar erro para código de DRE vazio."""
        with pytest.raises(ValueError):
            UnidadeIntegracaoService.get_unidade_supervisao_by_dre("")

    @patch(
        "apps.unidades.services.unidades_service."
        "SUPERVISAO_ESCOLAR_DRES_MAP"
    )
    def test_sem_mapeamento(self, mock_map):
        """Deve lançar erro quando não houver mapeamento."""
        mock_map.get.return_value = None

        with pytest.raises(ValueError):
            UnidadeIntegracaoService.get_unidade_supervisao_by_dre(
                "10",
            )

    @patch(
        "apps.unidades.services.unidades_service."
        "SUPERVISAO_ESCOLAR_DRES_MAP"
    )
    @patch.object(BaseEOLService, "_get")
    @patch("apps.unidades.services.unidades_service.env")
    def test_resposta_invalida(
        self,
        mock_env,
        mock_get,
        mock_map,
        mock_env_config,
    ):
        """Deve lançar erro para resposta inválida da supervisão."""
        mock_env.side_effect = mock_env_config()
        mock_map.get.return_value = "123"

        mock_get.return_value = []

        with pytest.raises(EOLUnexpectedResponseError):
            UnidadeIntegracaoService.get_unidade_supervisao_by_dre(
                "10",
            )

    @patch(
        "apps.unidades.services.unidades_service."
        "SUPERVISAO_ESCOLAR_DRES_MAP"
    )
    @patch.object(BaseEOLService, "_get")
    @patch("apps.unidades.services.unidades_service.env")
    def test_propagacao_erro_integracao(
        self,
        mock_env,
        mock_get,
        mock_map,
        mock_env_config,
    ):
        """Deve propagar erro de integração do serviço."""
        mock_env.side_effect = mock_env_config()
        mock_map.get.return_value = "123"

        mock_get.side_effect = EOLIntegrationError("erro")

        with pytest.raises(EOLIntegrationError):
            UnidadeIntegracaoService.get_unidade_supervisao_by_dre(
                "10",
            )

    @patch(
        "apps.unidades.services.unidades_service."
        "SUPERVISAO_ESCOLAR_DRES_MAP"
    )
    @patch.object(BaseEOLService, "_get")
    @patch("apps.unidades.services.unidades_service.env")
    def test_propagacao_timeout(
        self,
        mock_env,
        mock_get,
        mock_map,
        mock_env_config,
    ):
        """Deve propagar erro de timeout do serviço."""
        mock_env.side_effect = mock_env_config()
        mock_map.get.return_value = "123"

        mock_get.side_effect = EOLTimeoutError("timeout")

        with pytest.raises(EOLTimeoutError):
            UnidadeIntegracaoService.get_unidade_supervisao_by_dre(
                "10",
            )

    @patch(
        "apps.unidades.services.unidades_service."
        "SUPERVISAO_ESCOLAR_DRES_MAP"
    )
    @patch.object(BaseEOLService, "_get")
    @patch("apps.unidades.services.unidades_service.env")
    def test_propagacao_erro_comunicacao(
        self,
        mock_env,
        mock_get,
        mock_map,
        mock_env_config,
    ):
        """Deve propagar erro de comunicação do serviço."""
        mock_env.side_effect = mock_env_config()
        mock_map.get.return_value = "123"

        mock_get.side_effect = EOLCommunicationError("erro")

        with pytest.raises(EOLCommunicationError):
            UnidadeIntegracaoService.get_unidade_supervisao_by_dre(
                "10",
            )


# ================= COBERTURA EXTRA =================


class TestCoberturaExtra:
    """Testa casos extras de cobertura de código."""

    @patch.object(DREIntegracaoService, "get_dres")
    def test_get_dre_by_codigo_propaga_permission(
        self,
        mock_get_dres,
    ):
        """Deve propagar PermissionError da integração."""
        mock_get_dres.side_effect = PermissionError("erro")

        with pytest.raises(PermissionError):
            DREIntegracaoService.get_dre_by_codigo("1")

    @patch.object(DREIntegracaoService, "get_dres")
    def test_get_dre_by_codigo_propaga_eol(
        self,
        mock_get_dres,
    ):
        """Deve propagar erro de integração EOL."""
        mock_get_dres.side_effect = EOLIntegrationError("erro")

        with pytest.raises(EOLIntegrationError):
            DREIntegracaoService.get_dre_by_codigo("1")

    def test_get_unidades_tipo_codigo_invalido(self):
        """Deve lançar erro para código inválido de unidade."""
        with pytest.raises(ValueError):
            UnidadeIntegracaoService.get_unidades_by_dre_com_tipo_unidade(
                "",
            )

    def test_get_codigo_integracao_codigo_invalido(self):
        """Deve lançar erro para código inválido de integração."""
        with pytest.raises(ValueError):
            (
                UnidadeIntegracaoService.get_unidades_codigo_integracao_by_dre(
                    ""
                )
            )

    @patch("apps.unidades.services.unidades_service.env")
    @patch.object(BaseEOLService, "_get")
    def test_get_unidades_tipo_resposta_invalida(
        self,
        mock_get,
        mock_env,
        mock_env_config,
        codigo_dre_valido,
    ):
        """Deve lançar erro para resposta inválida de tipo unidade."""
        mock_env.side_effect = mock_env_config()
        mock_get.return_value = {}

        with pytest.raises(EOLUnexpectedResponseError):
            (
                UnidadeIntegracaoService.get_unidades_by_dre_com_tipo_unidade(
                    codigo_dre_valido,
                )
            )

    @patch("apps.unidades.services.unidades_service.env")
    @patch.object(BaseEOLService, "_get")
    def test_get_codigo_integracao_resposta_invalida(
        self,
        mock_get,
        mock_env,
        mock_env_config,
        codigo_dre_valido,
    ):
        """Deve lançar erro para resposta inválida de integração."""
        mock_env.side_effect = mock_env_config()
        mock_get.return_value = {}

        with pytest.raises(EOLUnexpectedResponseError):
            (
                UnidadeIntegracaoService.get_unidades_codigo_integracao_by_dre(
                    codigo_dre_valido,
                )
            )
