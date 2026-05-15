import pytest
from django.contrib.auth import get_user_model
from django.urls import reverse
from django.utils import timezone
from rest_framework import status
from rest_framework.test import APIClient

from apps.designacao.models.apostila import Apostila
from apps.designacao.models.designacao import Designacao

User = get_user_model()


@pytest.fixture
def api_client(django_user_model):
    client = APIClient()
    user = django_user_model.objects.create_user(
        username="testuser_apostila", password="password123"
    )
    client.force_authenticate(user=user)
    return client


@pytest.fixture
def designacao(db):
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
        tipo_vaga=Designacao.TipoVaga.DISPONIVEL,
    )


@pytest.fixture
def apostila(db, designacao):
    return Apostila.objects.create(
        tipo=Apostila.Tipo.APOSTILA,
        designacao=designacao,
        sei_numero="555",
        observacao="Obs Teste",
        d_o="2026-01-01",
    )


@pytest.mark.django_db
class TestApostilaViewSet:

    def test_list_apostilas(self, api_client, apostila):
        url = reverse("designacao:apostilas")
        response = api_client.get(url)
        assert response.status_code == status.HTTP_200_OK

    def test_retrieve_apostila(self, api_client, apostila):
        url = reverse("designacao:apostila-detail", kwargs={"pk": apostila.id})
        response = api_client.get(url)
        assert response.status_code == status.HTTP_200_OK
        assert response.data["id"] == apostila.id

    def test_create_apostila_sucesso(self, api_client, designacao):
        url = reverse("designacao:apostilas")
        data = {
            "designacao": designacao.id,
            "ato_apostilado": "designacao",
            "tipo": Apostila.Tipo.APOSTILA,
            "sei_numero": "999",
            "observacao": "Criado via View",
        }
        response = api_client.post(url, data, format="json")
        assert response.status_code == status.HTTP_201_CREATED
        assert Apostila.objects.filter(designacao=designacao).exists()

    def test_create_apostila_erro_validacao(self, api_client):
        url = reverse("designacao:apostilas")
        response = api_client.post(url, {}, format="json")
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_retrieve_apostila_nao_encontrada(self, api_client):
        url = reverse("designacao:apostila-detail", kwargs={"pk": 9999})
        response = api_client.get(url)
        assert response.status_code == status.HTTP_404_NOT_FOUND
