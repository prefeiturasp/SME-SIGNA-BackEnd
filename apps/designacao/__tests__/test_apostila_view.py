import pytest
from unittest.mock import patch
from django.core.exceptions import ValidationError
from django.urls import reverse
from rest_framework import status
from apps.designacao.models.apostila import Apostila
from apps.designacao.models.designacao import Designacao
from django.utils import timezone
from rest_framework.test import APIClient
from rest_framework.exceptions import ValidationError as DRFValidationError

@pytest.mark.django_db
class TestApostilaViewSet:

    @pytest.fixture
    def api_client(self, django_user_model):
        """Cria um usuário e autentica o cliente do DRF"""
        client = APIClient()
        user = django_user_model.objects.create_user(
            username="testuser", 
            password="password123"
        )
        client.force_authenticate(user=user)
        return client

    @pytest.fixture
    def designacao(self):
        return Designacao.objects.create(
            dre_nome="DRE TESTE",
            unidade_proponente="EMEF",
            codigo_hierarquico="1",
            indicado_nome_civil="USER",
            indicado_nome_servidor="USER",
            indicado_rf="1234567",
            indicado_vinculo=1,
            indicado_cargo_base="PROF",
            indicado_lotacao="L",
            indicado_local_exercicio="L",
            numero_portaria="123",
            ano_vigente="2026",
            sei_numero="111",
            data_inicio=timezone.now().date(),
            tipo_vaga=Designacao.TipoVaga.DISPONIVEL
        )

    @pytest.fixture
    def apostila(self, designacao):
        return Apostila.objects.create(
            tipo=Apostila.Tipo.APOSTILA,
            designacao=designacao,
            sei_numero="555",
            observacao="Obs Inicial"
        )

    def test_list_apostilas(self, api_client, apostila):
        """Testa GET /apostilas/"""
        url = reverse('designacao:apostilas') 
        response = api_client.get(url)
        
        assert response.status_code == status.HTTP_200_OK
        
        if isinstance(response.data, dict) and 'results' in response.data:
            assert any(item['sei_numero'] == "555" for item in response.data['results'])
        else:
            assert any(item['sei_numero'] == "555" for item in response.data)

    def test_retrieve_apostila(self, api_client, apostila):
        """Testa GET /apostilas/<id>/"""
        url = reverse('designacao:apostila-detail', kwargs={'pk': apostila.id})
        response = api_client.get(url)
        
        assert response.status_code == status.HTTP_200_OK
        assert response.data['sei_numero'] == "555"

    def test_create_apostila_sucesso(self, api_client, designacao):
        """Testa POST /apostilas/"""
        url = reverse('designacao:apostilas')
        data = {
            "designacao": designacao.id,
            "ato_apostilado": "designacao",
            "tipo": Apostila.Tipo.APOSTILA,
            "sei_numero": "999",
            "observacao": "Criado via View"
        }
        response = api_client.post(url, data, format='json')
        
        assert response.status_code == status.HTTP_201_CREATED
        assert Apostila.objects.filter(sei_numero="999").exists()

    def test_create_apostila_erro_validacao(self, api_client):
        """Testa POST inválido"""
        url = reverse('designacao:apostilas')
        response = api_client.post(url, {}, format='json')
        
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_filter_apostila_by_designacao(self, api_client, designacao, apostila):
        """Testa filtro via Query Params"""
        base_url = reverse('designacao:apostilas')
        url = f"{base_url}?designacao={designacao.id}"
        response = api_client.get(url)
        
        assert response.status_code == status.HTTP_200_OK

    def test_retrieve_apostila_nao_encontrada(self, api_client):
        """Testa 404"""
        url = reverse('designacao:apostila-detail', kwargs={'pk': 9999})
        response = api_client.get(url)
        
        assert response.status_code == status.HTTP_404_NOT_FOUND

    @patch('apps.designacao.api.views.apostila_view.ApostilaService.criar_apostila')
    def test_create_apostila_validation_error_exception(self, mock_service, api_client, designacao):
        url = reverse('designacao:apostilas') 
        
        data = {
            "designacao": designacao.id,
            "ato_apostilado": "designacao",
            "tipo": Apostila.Tipo.APOSTILA,
            "sei_numero": "999",
            "observacao": "Teste"
        }

        mock_service.side_effect = DRFValidationError("Erro do Service")
        
        response = api_client.post(url, data, format='json')
        
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "Erro do Service" in str(response.data)