"""Testes para a view de designação por unidade."""

import secrets
from unittest.mock import patch

import pytest
from rest_framework import status
from rest_framework.test import APIClient

from apps.helpers.exceptions import SmeIntegracaoError


@pytest.mark.django_db
class TestDesignacaoUnidadeView:
    """Testes para designacao unidade view."""

    password = secrets.token_urlsafe(16)

    def setup_method(self):
        """Método setup method."""
        self.client = APIClient()
        self.url = "/api/designacao/unidade/"

    @patch(
        "apps.designacao.api.views.designacao_unidades_view."
        "DesignacaoUnidadeService.obter_informacoes_escolares"
    )
    def test_get_sucesso(self, mock_service, django_user_model):
        """Verifica get sucesso."""
        user = django_user_model.objects.create_user(
            username="user", password=self.password
        )
        self.client.force_authenticate(user=user)

        mock_service.return_value = {"funcionarios_unidade": {}}

        response = self.client.get(self.url, {"codigo_ue": "UE_TESTE"})

        assert response.status_code == status.HTTP_200_OK
        assert response.json() == {"funcionarios_unidade": {}}

    def test_get_sem_codigo_ue(self, django_user_model):
        """Verifica get sem codigo ue."""
        user = django_user_model.objects.create_user(
            username="user", password=self.password
        )
        self.client.force_authenticate(user=user)

        response = self.client.get(self.url)

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert response.json() == {"detail": "codigo_ue é obrigatório"}

    @patch(
        "apps.designacao.api.views.designacao_unidades_view."
        "DesignacaoUnidadeService.obter_informacoes_escolares"
    )
    def test_get_erro_integracao_sme(
        self,
        mock_service,
        django_user_model,
    ):
        """Verifica get erro integracao sme."""
        user = django_user_model.objects.create_user(
            username="user", password=self.password
        )
        self.client.force_authenticate(user=user)

        mock_service.side_effect = SmeIntegracaoError("Erro integração SME")

        response = self.client.get(self.url, {"codigo_ue": "UE_TESTE"})

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert response.json() == {"detail": "Erro integração SME"}

    @patch(
        "apps.designacao.api.views.designacao_unidades_view."
        "DesignacaoUnidadeService.obter_informacoes_escolares"
    )
    def test_get_erro_inesperado(
        self,
        mock_service,
        django_user_model,
    ):
        """Verifica get erro inesperado."""
        user = django_user_model.objects.create_user(
            username="user", password=self.password
        )
        self.client.force_authenticate(user=user)

        mock_service.side_effect = Exception("boom")

        response = self.client.get(self.url, {"codigo_ue": "UE_TESTE"})

        assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR

    def test_get_nao_autenticado(self):
        """Verifica get nao autenticado."""
        response = self.client.get(self.url, {"codigo_ue": "UE_TESTE"})

        assert response.status_code == status.HTTP_401_UNAUTHORIZED


@pytest.mark.django_db
class TestDesignacaoUnidadeCargosView:
    """Testes para designacao unidade cargos view."""

    password = secrets.token_urlsafe(16)

    def setup_method(self):
        """Método setup method."""
        self.client = APIClient()
        self.url = "/api/designacao/unidade/cargos/"

    @patch(
        "apps.designacao.services.designacao_unidades_service.DesignacaoUnidadeService.listar_cargos_vaga"
    )
    def test_get_cargos_sucesso(self, mock_listar_cargos, django_user_model):
        """Verifica get cargos sucesso."""
        user = django_user_model.objects.create_user(
            username="user_cargos", password=self.password
        )
        self.client.force_authenticate(user=user)

        # Mock do retorno esperado da service
        mock_data = [
            {"codigoCargo": 3360, "nomeCargo": "DIRETOR DE ESCOLA"},
            {"codigoCargo": 3379, "nomeCargo": "COORDENADOR PEDAGOGICO"},
        ]
        mock_listar_cargos.return_value = mock_data

        response = self.client.get(self.url)

        assert response.status_code == status.HTTP_200_OK
        assert len(response.json()) == 2
        assert response.json() == mock_data
        mock_listar_cargos.assert_called_once()

    def test_get_cargos_nao_autenticado(self):
        """Verifica get cargos nao autenticado."""
        response = self.client.get(self.url)

        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    @patch(
        "apps.designacao.services.designacao_unidades_service.DesignacaoUnidadeService.listar_cargos_vaga"
    )
    def test_get_cargos_erro_interno(
        self, mock_listar_cargos, django_user_model
    ):
        """Verifica get cargos erro interno."""
        user = django_user_model.objects.create_user(
            username="user_erro", password=self.password
        )
        self.client.force_authenticate(user=user)

        mock_listar_cargos.side_effect = Exception("Erro inesperado")

        response = self.client.get(self.url)

        assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
        assert response.json() == {"detail": "Erro interno ao buscar cargos"}
