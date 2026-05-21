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

    @patch("apps.unidades.services.unidades_service.requests.get")
    def test_get_sucesso_dict(self, mock_get):
        mock_response = Mock(status_code=200)
        mock_response.json.return_value = {"ok": True}
        mock_get.return_value = mock_response

        result = BaseEOLService._get("url", "ctx")

        assert result == {"ok": True}

    @patch("apps.unidades.services.unidades_service.requests.get")
    def test_get_401(self, mock_get):
        mock_get.return_value = Mock(status_code=401)

        with pytest.raises(PermissionError):
            BaseEOLService._get("url", "ctx")

    @patch("apps.unidades.services.unidades_service.requests.get")
    def test_get_404(self, mock_get):
        mock_get.return_value = Mock(status_code=404)

        with pytest.raises(LookupError):
            BaseEOLService._get("url", "ctx")

    @patch("apps.unidades.services.unidades_service.requests.get")
    def test_get_status_erro(self, mock_get):
        mock_response = Mock(status_code=500, text="erro")
        mock_get.return_value = mock_response

        with pytest.raises(EOLIntegrationError):
            BaseEOLService._get("url", "ctx")

    @patch("apps.unidades.services.unidades_service.requests.get")
    def test_get_timeout(self, mock_get):
        mock_get.side_effect = requests.exceptions.Timeout()

        with pytest.raises(EOLTimeoutError):
            BaseEOLService._get("url", "ctx")

    @patch("apps.unidades.services.unidades_service.requests.get")
    def test_get_request_exception(self, mock_get):
        mock_get.side_effect = requests.exceptions.RequestException("erro")

        with pytest.raises(EOLCommunicationError):
            BaseEOLService._get("url", "ctx")


# ================= DRE =================


class TestDREIntegracaoService:

    @patch("apps.unidades.services.unidades_service.env")
    @patch.object(BaseEOLService, "_get")
    def test_get_dres(
        self, mock_get, mock_env, mock_env_config, mock_dres_response
    ):
        mock_env.side_effect = mock_env_config()
        mock_get.return_value = mock_dres_response

        result = DREIntegracaoService.get_dres()

        assert result == mock_dres_response

    @patch("apps.unidades.services.unidades_service.env")
    @patch.object(BaseEOLService, "_get")
    def test_get_dres_resposta_invalida(
        self, mock_get, mock_env, mock_env_config
    ):
        mock_env.side_effect = mock_env_config()
        mock_get.return_value = {}

        with pytest.raises(EOLUnexpectedResponseError):
            DREIntegracaoService.get_dres()

    @patch.object(DREIntegracaoService, "get_dres")
    def test_get_dre_by_codigo_encontrada(
        self, mock_get_dres, mock_dres_response, codigo_dre_valido
    ):
        mock_get_dres.return_value = mock_dres_response

        result = DREIntegracaoService.get_dre_by_codigo(codigo_dre_valido)

        assert result["codigoDRE"] == codigo_dre_valido

    @patch.object(DREIntegracaoService, "get_dres")
    def test_get_dre_by_codigo_none(self, mock_get_dres):
        mock_get_dres.return_value = []

        assert DREIntegracaoService.get_dre_by_codigo("1") is None


# ================= UNIDADES =================


class TestUnidadeIntegracaoService:

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
        mock_env.side_effect = mock_env_config()
        mock_get.return_value = mock_unidades_response

        result = UnidadeIntegracaoService.get_unidades_by_dre(
            codigo_dre_valido
        )

        assert result == mock_unidades_response

    @patch.object(BaseEOLService, "_get")
    def test_get_unidades_codigo_invalido(self, mock_get):
        with pytest.raises(ValueError):
            UnidadeIntegracaoService.get_unidades_by_dre("")

        mock_get.assert_not_called()

    @patch("apps.unidades.services.unidades_service.env")
    @patch.object(BaseEOLService, "_get")
    def test_get_unidades_resposta_invalida(
        self, mock_get, mock_env, mock_env_config, codigo_dre_valido
    ):
        mock_env.side_effect = mock_env_config()
        mock_get.return_value = {}

        with pytest.raises(EOLUnexpectedResponseError):
            UnidadeIntegracaoService.get_unidades_by_dre(codigo_dre_valido)

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
        mock_env.side_effect = mock_env_config()
        mock_get.return_value = mock_unidades_response

        result = UnidadeIntegracaoService.get_unidades_by_dre_com_tipo_unidade(
            codigo_dre_valido
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
        mock_env.side_effect = mock_env_config()
        mock_get.return_value = mock_unidades_response

        result = (
            UnidadeIntegracaoService.get_unidades_codigo_integracao_by_dre(
                codigo_dre_valido
            )
        )

        assert result == mock_unidades_response


# ================= SUPERVISAO (REFATORADO) =================


class TestUnidadeSupervisao:

    @patch(
        "apps.unidades.services.unidades_service.SUPERVISAO_ESCOLAR_DRES_MAP"
    )
    @patch.object(BaseEOLService, "_get")
    @patch("apps.unidades.services.unidades_service.env")
    def test_sucesso(self, mock_env, mock_get, mock_map, mock_env_config):
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
        with pytest.raises(ValueError):
            UnidadeIntegracaoService.get_unidade_supervisao_by_dre("")

    @patch(
        "apps.unidades.services.unidades_service.SUPERVISAO_ESCOLAR_DRES_MAP"
    )
    def test_sem_mapeamento(self, mock_map):
        mock_map.get.return_value = None

        with pytest.raises(ValueError):
            UnidadeIntegracaoService.get_unidade_supervisao_by_dre("10")

    @patch(
        "apps.unidades.services.unidades_service.SUPERVISAO_ESCOLAR_DRES_MAP"
    )
    @patch.object(BaseEOLService, "_get")
    @patch("apps.unidades.services.unidades_service.env")
    def test_resposta_invalida(
        self, mock_env, mock_get, mock_map, mock_env_config
    ):
        mock_env.side_effect = mock_env_config()
        mock_map.get.return_value = "123"

        mock_get.return_value = []

        with pytest.raises(EOLUnexpectedResponseError):
            UnidadeIntegracaoService.get_unidade_supervisao_by_dre("10")

    @patch(
        "apps.unidades.services.unidades_service.SUPERVISAO_ESCOLAR_DRES_MAP"
    )
    @patch.object(BaseEOLService, "_get")
    @patch("apps.unidades.services.unidades_service.env")
    def test_propagacao_erro_integracao(
        self, mock_env, mock_get, mock_map, mock_env_config
    ):
        mock_env.side_effect = mock_env_config()
        mock_map.get.return_value = "123"

        mock_get.side_effect = EOLIntegrationError("erro")

        with pytest.raises(EOLIntegrationError):
            UnidadeIntegracaoService.get_unidade_supervisao_by_dre("10")

    @patch(
        "apps.unidades.services.unidades_service.SUPERVISAO_ESCOLAR_DRES_MAP"
    )
    @patch.object(BaseEOLService, "_get")
    @patch("apps.unidades.services.unidades_service.env")
    def test_propagacao_timeout(
        self, mock_env, mock_get, mock_map, mock_env_config
    ):
        mock_env.side_effect = mock_env_config()
        mock_map.get.return_value = "123"

        mock_get.side_effect = EOLTimeoutError("timeout")

        with pytest.raises(EOLTimeoutError):
            UnidadeIntegracaoService.get_unidade_supervisao_by_dre("10")

    @patch(
        "apps.unidades.services.unidades_service.SUPERVISAO_ESCOLAR_DRES_MAP"
    )
    @patch.object(BaseEOLService, "_get")
    @patch("apps.unidades.services.unidades_service.env")
    def test_propagacao_erro_comunicacao(
        self, mock_env, mock_get, mock_map, mock_env_config
    ):
        mock_env.side_effect = mock_env_config()
        mock_map.get.return_value = "123"

        mock_get.side_effect = EOLCommunicationError("erro")

        with pytest.raises(EOLCommunicationError):
            UnidadeIntegracaoService.get_unidade_supervisao_by_dre("10")


# ================= COBERTURA EXTRA =================


class TestCoberturaExtra:

    @patch.object(DREIntegracaoService, "get_dres")
    def test_get_dre_by_codigo_propaga_permission(self, mock_get_dres):
        mock_get_dres.side_effect = PermissionError("erro")

        with pytest.raises(PermissionError):
            DREIntegracaoService.get_dre_by_codigo("1")

    @patch.object(DREIntegracaoService, "get_dres")
    def test_get_dre_by_codigo_propaga_eol(self, mock_get_dres):
        mock_get_dres.side_effect = EOLIntegrationError("erro")

        with pytest.raises(EOLIntegrationError):
            DREIntegracaoService.get_dre_by_codigo("1")

    def test_get_unidades_tipo_codigo_invalido(self):
        with pytest.raises(ValueError):
            UnidadeIntegracaoService.get_unidades_by_dre_com_tipo_unidade("")

    def test_get_codigo_integracao_codigo_invalido(self):
        with pytest.raises(ValueError):
            UnidadeIntegracaoService.get_unidades_codigo_integracao_by_dre("")

    @patch("apps.unidades.services.unidades_service.env")
    @patch.object(BaseEOLService, "_get")
    def test_get_unidades_tipo_resposta_invalida(
        self, mock_get, mock_env, mock_env_config, codigo_dre_valido
    ):
        mock_env.side_effect = mock_env_config()
        mock_get.return_value = {}

        with pytest.raises(EOLUnexpectedResponseError):
            UnidadeIntegracaoService.get_unidades_by_dre_com_tipo_unidade(
                codigo_dre_valido
            )

    @patch("apps.unidades.services.unidades_service.env")
    @patch.object(BaseEOLService, "_get")
    def test_get_codigo_integracao_resposta_invalida(
        self, mock_get, mock_env, mock_env_config, codigo_dre_valido
    ):
        mock_env.side_effect = mock_env_config()
        mock_get.return_value = {}

        with pytest.raises(EOLUnexpectedResponseError):
            UnidadeIntegracaoService.get_unidades_codigo_integracao_by_dre(
                codigo_dre_valido
            )
