"""Testes do UnidadeViewSet."""

from unittest.mock import patch

import pytest
from rest_framework import status
from rest_framework.request import Request
from rest_framework.test import APIRequestFactory

from apps.unidades.api.views.unidades_viewset import UnidadeViewSet


class TestUnidadeViewSet:
    """Testes para o UnidadeViewSet."""

    @pytest.fixture
    def factory(self):
        """Fixture para criar requests de teste."""
        return APIRequestFactory()

    @pytest.fixture
    def viewset(self):
        """Fixture para instanciar o ViewSet."""
        return UnidadeViewSet()

    @pytest.fixture
    def mock_dres(self):
        """Fixture com dados mockados de DREs."""
        return [
            {
                "codigo_dre": "108200",
                "nome_dre": "Diretoria Regional de Educação Butantã",
                "sigla_dre": "DRE-BT",
            },
            {
                "codigo_dre": "108300",
                "nome_dre": "Diretoria Regional de Educação Campo Limpo",
                "sigla_dre": "DRE-CL",
            },
        ]

    @pytest.fixture
    def mock_ues(self):
        """Fixture com dados mockados de UEs."""
        return [
            {
                "codigo_eol": "019456",
                "nome_oficial": "EMEF - Escola Municipal de Ensino Fundamental",
                "tipo_ue": "EMEF",
                "nome_dre": "DRE Butantã",
            },
            {
                "codigo_eol": "019457",
                "nome_oficial": "EMEI - Escola Municipal de Educação Infantil",
                "tipo_ue": "EMEI",
                "nome_dre": "DRE Butantã",
            },
        ]

    def _create_request(
        self, factory, method="get", path="/api/unidades/", data=None
    ):
        """Cria uma Request DRF válida para uso nos testes."""
        if method == "get":
            wsgi_request = factory.get(path, data or {})
        else:
            wsgi_request = factory.post(path, data or {})
        return Request(wsgi_request)

    # ==================== TESTES DE LISTAGEM DE DREs ====================

    @patch(
        "apps.unidades.api.views.unidades_viewset.DREIntegracaoService.get_dres"
    )
    def test_listar_dres_sucesso(
        self, mock_get_dres, factory, viewset, mock_dres
    ):
        """Testa listagem de DREs com sucesso."""
        mock_get_dres.return_value = mock_dres

        request = self._create_request(factory, data={"tipo": "DRE"})
        response = viewset.list(request)

        assert response.status_code == status.HTTP_200_OK
        assert len(response.data) == 2
        assert response.data == mock_dres
        mock_get_dres.assert_called_once()

    @patch(
        "apps.unidades.api.views.unidades_viewset.DREIntegracaoService.get_dres"
    )
    def test_listar_dres_vazio(self, mock_get_dres, factory, viewset):
        """Testa listagem de DREs quando não há resultados."""
        mock_get_dres.return_value = []

        request = self._create_request(factory, data={"tipo": "DRE"})
        response = viewset.list(request)

        assert response.status_code == status.HTTP_200_OK
        assert response.data == []

    @patch(
        "apps.unidades.api.views.unidades_viewset.DREIntegracaoService.get_dres"
    )
    def test_listar_dres_erro_permissao(self, mock_get_dres, factory, viewset):
        """Testa erro de permissão ao listar DREs."""
        mock_get_dres.side_effect = PermissionError(
            "Token inválido ou expirado"
        )

        request = self._create_request(factory, data={"tipo": "DRE"})
        response = viewset.list(request)

        assert response.status_code == status.HTTP_401_UNAUTHORIZED
        assert "detail" in response.data
        assert "Token inválido" in response.data["detail"]

    @patch(
        "apps.unidades.api.views.unidades_viewset.DREIntegracaoService.get_dres"
    )
    def test_listar_dres_erro_generico(self, mock_get_dres, factory, viewset):
        """Testa erro genérico ao listar DREs."""
        mock_get_dres.side_effect = Exception("Erro de conexão")

        request = self._create_request(factory, data={"tipo": "DRE"})
        response = viewset.list(request)

        assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
        assert "detail" in response.data
        assert "Erro ao consultar DREs" in response.data["detail"]

    # ==================== TESTES DE LISTAGEM DE UEs ====================

    @patch(
        "apps.unidades.api.views.unidades_viewset.UnidadeIntegracaoService.get_unidade_supervisao_by_dre"
    )
    @patch(
        "apps.unidades.api.views.unidades_viewset.UnidadeIntegracaoService.get_unidades_by_dre_com_tipo_unidade"
    )
    def test_listar_ues_sucesso(
        self, mock_get_ues, mock_get_supervisao, factory, viewset, mock_ues
    ):
        """Testa listagem de UEs com sucesso."""
        unidade_supervisao = {
            "codigoEscola": 108202,
            "nomeEscola": "SUPERVISAO DRE BUTANTA",
            "codigoDRE": "108200",
            "tipoEscola": 14,
            "siglaTipoEscola": "UA",
            "nomeDRE": "DIRETORIA REGIONAL DE EDUCACAO BUTANTA",
            "siglaDRE": "BT",
            "codigoSubprefeitura": None,
            "nomeSubprefeitura": None,
        }
        mock_get_ues.return_value = [*mock_ues]
        expected_response = [*mock_ues, unidade_supervisao]
        mock_get_supervisao.return_value = unidade_supervisao

        request = self._create_request(
            factory, data={"tipo": "UE", "dre": "108200"}
        )
        response = viewset.list(request)

        assert response.status_code == status.HTTP_200_OK
        assert len(response.data) == 3
        assert response.data == expected_response
        mock_get_ues.assert_called_once_with("108200")
        mock_get_supervisao.assert_called_once_with("108200")

    @patch(
        "apps.unidades.api.views.unidades_viewset.UnidadeIntegracaoService.get_unidade_supervisao_by_dre"
    )
    @patch(
        "apps.unidades.api.views.unidades_viewset.UnidadeIntegracaoService.get_unidades_by_dre_com_tipo_unidade"
    )
    def test_listar_ues_sem_codigo_dre(
        self, mock_get_ues, mock_get_supervisao, factory, viewset
    ):
        """Testa listagem de UEs sem informar código da DRE."""
        request = self._create_request(factory, data={"tipo": "UE"})
        response = viewset.list(request)

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "detail" in response.data
        assert "necessário informar o código da DRE" in response.data["detail"]
        mock_get_ues.assert_not_called()
        mock_get_supervisao.assert_not_called()

    @patch(
        "apps.unidades.api.views.unidades_viewset.UnidadeIntegracaoService.get_unidade_supervisao_by_dre"
    )
    @patch(
        "apps.unidades.api.views.unidades_viewset.UnidadeIntegracaoService.get_unidades_by_dre_com_tipo_unidade"
    )
    def test_listar_ues_codigo_dre_vazio(
        self, mock_get_ues, mock_get_supervisao, factory, viewset
    ):
        """Testa listagem de UEs com código da DRE vazio."""
        request = self._create_request(factory, data={"tipo": "UE", "dre": ""})
        response = viewset.list(request)

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "detail" in response.data
        mock_get_ues.assert_not_called()
        mock_get_supervisao.assert_not_called()

    @patch(
        "apps.unidades.api.views.unidades_viewset.UnidadeIntegracaoService.get_unidade_supervisao_by_dre"
    )
    @patch(
        "apps.unidades.api.views.unidades_viewset.UnidadeIntegracaoService.get_unidades_by_dre_com_tipo_unidade"
    )
    def test_listar_ues_valor_invalido(
        self, mock_get_ues, mock_get_supervisao, factory, viewset
    ):
        """Testa listagem de UEs com código da DRE inválido."""
        mock_get_ues.side_effect = ValueError(
            "Código da DRE deve ser numérico"
        )
        mock_get_supervisao.return_value = None

        request = self._create_request(
            factory, data={"tipo": "UE", "dre": "ABC"}
        )
        response = viewset.list(request)

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "detail" in response.data
        assert "numérico" in response.data["detail"]
        mock_get_supervisao.assert_called_once_with("ABC")

    @patch(
        "apps.unidades.api.views.unidades_viewset.UnidadeIntegracaoService.get_unidade_supervisao_by_dre"
    )
    @patch(
        "apps.unidades.api.views.unidades_viewset.UnidadeIntegracaoService.get_unidades_by_dre_com_tipo_unidade"
    )
    def test_listar_ues_dre_nao_encontrada(
        self, mock_get_ues, mock_get_supervisao, factory, viewset
    ):
        """Testa listagem de UEs quando DRE não existe."""
        mock_get_ues.side_effect = LookupError("DRE não encontrada")
        mock_get_supervisao.return_value = None

        request = self._create_request(
            factory, data={"tipo": "UE", "dre": "999999"}
        )
        response = viewset.list(request)

        assert response.status_code == status.HTTP_404_NOT_FOUND
        assert "detail" in response.data
        assert "não encontrada" in response.data["detail"]
        mock_get_supervisao.assert_called_once_with("999999")

    @patch(
        "apps.unidades.api.views.unidades_viewset.UnidadeIntegracaoService.get_unidade_supervisao_by_dre"
    )
    @patch(
        "apps.unidades.api.views.unidades_viewset.UnidadeIntegracaoService.get_unidades_by_dre_com_tipo_unidade"
    )
    def test_listar_ues_erro_permissao(
        self, mock_get_ues, mock_get_supervisao, factory, viewset
    ):
        """Testa erro de permissão ao listar UEs."""
        mock_get_ues.side_effect = PermissionError("Token inválido")
        mock_get_supervisao.return_value = None

        request = self._create_request(
            factory, data={"tipo": "UE", "dre": "108200"}
        )
        response = viewset.list(request)

        assert response.status_code == status.HTTP_401_UNAUTHORIZED
        assert "detail" in response.data
        mock_get_supervisao.assert_called_once_with("108200")

    @patch(
        "apps.unidades.api.views.unidades_viewset.UnidadeIntegracaoService.get_unidade_supervisao_by_dre"
    )
    @patch(
        "apps.unidades.api.views.unidades_viewset.UnidadeIntegracaoService.get_unidades_by_dre_com_tipo_unidade"
    )
    def test_listar_ues_erro_generico(
        self, mock_get_ues, mock_get_supervisao, factory, viewset
    ):
        """Testa erro genérico ao listar UEs."""
        mock_get_ues.side_effect = Exception("Erro de conexão")
        mock_get_supervisao.return_value = None

        request = self._create_request(
            factory, data={"tipo": "UE", "dre": "108200"}
        )
        response = viewset.list(request)

        assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
        assert "detail" in response.data
        assert "Erro ao consultar unidades" in response.data["detail"]
        mock_get_supervisao.assert_called_once_with("108200")

    @patch(
        "apps.unidades.api.views.unidades_viewset.UnidadeIntegracaoService.get_unidade_supervisao_by_dre"
    )
    @patch(
        "apps.unidades.api.views.unidades_viewset.UnidadeIntegracaoService.get_unidades_by_dre_com_tipo_unidade"
    )
    def test_listar_ues_vazio(
        self, mock_get_ues, mock_get_supervisao, factory, viewset
    ):
        """Testa listagem de UEs quando não há resultados."""
        unidade_supervisao = {
            "codigoEscola": 108202,
            "nomeEscola": "SUPERVISAO DRE BUTANTA",
            "codigoDRE": "108200",
            "tipoEscola": 14,
            "siglaTipoEscola": "UA",
            "nomeDRE": "DIRETORIA REGIONAL DE EDUCACAO BUTANTA",
            "siglaDRE": "BT",
            "codigoSubprefeitura": None,
            "nomeSubprefeitura": None,
        }
        mock_get_ues.return_value = []
        mock_get_supervisao.return_value = unidade_supervisao

        request = self._create_request(
            factory, data={"tipo": "UE", "dre": "108200"}
        )
        response = viewset.list(request)

        assert response.status_code == status.HTTP_200_OK
        assert response.data == [unidade_supervisao]
        mock_get_supervisao.assert_called_once_with("108200")

    @patch(
        "apps.unidades.api.views.unidades_viewset.UnidadeIntegracaoService.get_unidade_supervisao_by_dre"
    )
    @patch(
        "apps.unidades.api.views.unidades_viewset.UnidadeIntegracaoService.get_unidades_by_dre_com_tipo_unidade"
    )
    def test_listar_ues_sucesso_quando_supervisao_falha(
        self, mock_get_ues, mock_get_supervisao, factory, viewset, mock_ues
    ):
        """Testa que a listagem de UEs continua mesmo com erro na unidade de supervisão."""
        mock_get_ues.return_value = mock_ues
        mock_get_supervisao.side_effect = Exception("Erro supervisão")

        request = self._create_request(
            factory, data={"tipo": "UE", "dre": "108200"}
        )
        response = viewset.list(request)

        assert response.status_code == status.HTTP_200_OK
        assert response.data == mock_ues
        mock_get_ues.assert_called_once_with("108200")
        mock_get_supervisao.assert_called_once_with("108200")

    # ==================== TESTES DE VALIDAÇÃO DE PARÂMETROS ====================

    def test_sem_parametro_tipo(self, factory, viewset):
        """Testa requisição sem parâmetro 'tipo'."""
        request = self._create_request(factory)
        response = viewset.list(request)

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "detail" in response.data
        assert "necessário informar o parâmetro" in response.data["detail"]

    def test_parametro_tipo_invalido(self, factory, viewset):
        """Testa requisição com parâmetro 'tipo' inválido."""
        request = self._create_request(factory, data={"tipo": "INVALIDO"})
        response = viewset.list(request)

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "detail" in response.data
        assert "inválido" in response.data["detail"]
        assert "DRE" in response.data["detail"]
        assert "UE" in response.data["detail"]

    def test_parametro_tipo_case_sensitive(self, factory, viewset):
        """Testa que o parâmetro 'tipo' é case-sensitive."""
        request = self._create_request(factory, data={"tipo": "dre"})
        response = viewset.list(request)

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "detail" in response.data

    # ==================== TESTES DE PERMISSÕES ====================

    def test_permission_classes(self, viewset):
        """Testa que o ViewSet permite acesso público."""
        from rest_framework.permissions import AllowAny

        assert viewset.permission_classes == [AllowAny]

    # ==================== TESTES DE LOGGING ====================

    @patch("apps.unidades.api.views.unidades_viewset.logger")
    @patch(
        "apps.unidades.api.views.unidades_viewset.DREIntegracaoService.get_dres"
    )
    def test_logging_sucesso_dres(
        self, mock_get_dres, mock_logger, factory, viewset, mock_dres
    ):
        """Testa logging em caso de sucesso ao listar DREs."""
        mock_get_dres.return_value = mock_dres

        request = self._create_request(factory, data={"tipo": "DRE"})
        viewset.list(request)

        # Verifica se o log de info foi chamado
        assert mock_logger.info.call_count >= 1

    @patch("apps.unidades.api.views.unidades_viewset.logger")
    @patch(
        "apps.unidades.api.views.unidades_viewset.DREIntegracaoService.get_dres"
    )
    def test_logging_erro_dres(
        self, mock_get_dres, mock_logger, factory, viewset
    ):
        """Testa logging em caso de erro ao listar DREs."""
        mock_get_dres.side_effect = Exception("Erro de teste")

        request = self._create_request(factory, data={"tipo": "DRE"})
        viewset.list(request)

        # Verifica se o log de erro foi chamado
        mock_logger.error.assert_called()

    @patch("apps.unidades.api.views.unidades_viewset.logger")
    def test_logging_parametro_invalido(self, mock_logger, factory, viewset):
        """Testa logging quando parâmetro é inválido."""
        request = self._create_request(factory, data={"tipo": "INVALIDO"})
        viewset.list(request)

        # Verifica se o log de warning foi chamado
        mock_logger.warning.assert_called()


class TestUnidadeViewSetContextoDesignacao:
    """Testes do parâmetro ``contexto=designacao``."""

    PATCH_DRES = (
        "apps.unidades.api.views.unidades_viewset."
        "DREIntegracaoService.get_dres"
    )
    PATCH_UES = (
        "apps.unidades.api.views.unidades_viewset."
        "UnidadeIntegracaoService.get_unidades_by_dre_com_tipo_unidade"
    )
    PATCH_SUPERVISAO = (
        "apps.unidades.api.views.unidades_viewset."
        "UnidadeIntegracaoService.get_unidade_supervisao_by_dre"
    )

    DRE_ATUAL = {
        "codigoDRE": "108200",
        "nomeDRE": "DIRETORIA REGIONAL DE EDUCACAO CAMPO LIMPO",
        "siglaDRE": "DRE - CL",
    }
    COORDENADORIA = {
        "codigoDRE": "105700",
        "nomeDRE": "COORDENADORIA DE EDUCACAO CAMPO LIMPO",
        "siglaDRE": "COORDENADORIA DE EDUCACAO CAMPO IIMPO",
    }
    NAE = {
        "codigoDRE": "100013",
        "nomeDRE": "NUCLEO DE ACAO EDUCATIVA - NAE-01",
        "siglaDRE": "NAE-01",
    }

    SUPERVISAO = {
        "codigoEscola": 108202,
        "nomeEscola": "SUPERVISAO DRE CAMPO LIMPO",
        "codigoDRE": "108200",
        "siglaTipoEscola": "UA",
    }

    @staticmethod
    def _ue(codigo: str, sigla: str) -> dict:
        return {"codigoEscola": codigo, "siglaTipoEscola": sigla}

    @pytest.fixture
    def viewset(self):
        return UnidadeViewSet()

    @staticmethod
    def _listar(viewset, **params):
        request = Request(APIRequestFactory().get("/api/unidades/", params))
        return viewset.list(request)

    @pytest.fixture
    def dres(self):
        return [self.DRE_ATUAL, self.COORDENADORIA, self.NAE]

    @pytest.fixture
    def ues(self):
        return [
            self._ue("019751", "EMEF"),
            self._ue("019537", "EMEI        "),
            self._ue("123456", "mova"),
            self._ue("305316", "ESC.PART."),
            self._ue("306229", "CR.P.CONV"),
            self._ue("999999", None),
        ]

    def test_dres_com_contexto_mantem_so_as_atuais(self, viewset, dres):
        with patch(self.PATCH_DRES, return_value=dres):
            response = self._listar(viewset, tipo="DRE", contexto="designacao")

        assert response.status_code == status.HTTP_200_OK
        assert response.data == [self.DRE_ATUAL]

    def test_dres_sem_contexto_lista_todas(self, viewset, dres):
        with patch(self.PATCH_DRES, return_value=dres):
            response = self._listar(viewset, tipo="DRE")

        assert response.data == dres

    def test_ues_com_contexto_filtra_tipos_e_mantem_supervisao(
        self, viewset, ues
    ):
        with (
            patch(self.PATCH_UES, return_value=ues),
            patch(self.PATCH_SUPERVISAO, return_value=self.SUPERVISAO),
        ):
            response = self._listar(
                viewset, tipo="UE", dre="108200", contexto="designacao"
            )

        assert response.status_code == status.HTTP_200_OK
        assert [u["codigoEscola"] for u in response.data] == [
            "019751",
            "019537",
            "123456",
            108202,
        ]

    def test_ues_com_contexto_sem_supervisao(self, viewset, ues):
        with (
            patch(self.PATCH_UES, return_value=ues),
            patch(self.PATCH_SUPERVISAO, side_effect=ValueError("sem UA")),
        ):
            response = self._listar(
                viewset, tipo="UE", dre="108200", contexto="designacao"
            )

        assert [u["codigoEscola"] for u in response.data] == [
            "019751",
            "019537",
            "123456",
        ]

    def test_ues_sem_contexto_lista_todas(self, viewset, ues):
        with (
            patch(self.PATCH_UES, return_value=list(ues)),
            patch(self.PATCH_SUPERVISAO, return_value=self.SUPERVISAO),
        ):
            response = self._listar(viewset, tipo="UE", dre="108200")

        assert response.data == [*ues, self.SUPERVISAO]

    @pytest.mark.parametrize("contexto", ["outro", "", "DESIGNACAO"])
    def test_contexto_invalido_retorna_400(self, viewset, contexto):
        with patch(self.PATCH_DRES) as mock_dres:
            response = self._listar(viewset, tipo="DRE", contexto=contexto)

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "contexto" in response.data["detail"]
        mock_dres.assert_not_called()
