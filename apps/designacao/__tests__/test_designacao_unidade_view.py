import pytest
import secrets
from unittest.mock import patch

from rest_framework.test import APIClient
from rest_framework import status

from apps.helpers.exceptions import SmeIntegracaoException

@pytest.mark.django_db
class TestDesignacaoUnidadeView:

    password = secrets.token_urlsafe(16)

    def setup_method(self):
        self.client = APIClient()
        self.url = "/api/designacao/unidade/"
    @patch(
        "apps.designacao.api.views.designacao_unidades_view."
        "DesignacaoUnidadeService.obter_informacoes_escolares"
    )
    
    def test_get_sucesso(self, mock_service, django_user_model):
        user = django_user_model.objects.create_user(
            username="user",
            password=self.password
        )
        self.client.force_authenticate(user=user)

        mock_service.return_value = {"funcionarios_unidade": {}}

        response = self.client.get(
            self.url,
            {"codigo_ue": "UE_TESTE"}
        )

        assert response.status_code == status.HTTP_200_OK
        assert response.json() == {"funcionarios_unidade": {}}

    def test_get_sem_codigo_ue(self, django_user_model):
        user = django_user_model.objects.create_user(
            username="user",
            password=self.password
        )
        self.client.force_authenticate(user=user)

        response = self.client.get(self.url)

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert response.json() == {
            "detail": "codigo_ue é obrigatório"
        }
    @patch(
        "apps.designacao.api.views.designacao_unidades_view."
        "DesignacaoUnidadeService.obter_informacoes_escolares"
    )

    def test_get_erro_integracao_sme(
        self,
        mock_service,
        django_user_model,
    ):
        user = django_user_model.objects.create_user(
            username="user",
            password=self.password
        )
        self.client.force_authenticate(user=user)

        mock_service.side_effect = SmeIntegracaoException(
            "Erro integração SME"
        )

        response = self.client.get(
            self.url,
            {"codigo_ue": "UE_TESTE"}
        )

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert response.json() == {
            "detail": "Erro integração SME"
        }

    @patch(
        "apps.designacao.api.views.designacao_unidades_view."
        "DesignacaoUnidadeService.obter_informacoes_escolares"
    )
    def test_get_erro_inesperado(
        self,
        mock_service,
        django_user_model,
    ):
        user = django_user_model.objects.create_user(
            username="user",
            password=self.password
        )
        self.client.force_authenticate(user=user)

        mock_service.side_effect = Exception("boom")

        response = self.client.get(
            self.url,
            {"codigo_ue": "UE_TESTE"}
        )

        assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR

    def test_get_nao_autenticado(self):
        response = self.client.get(
            self.url,
            {"codigo_ue": "UE_TESTE"}
        )

        assert response.status_code == status.HTTP_401_UNAUTHORIZED

