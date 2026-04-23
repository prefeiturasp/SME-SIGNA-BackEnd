import pytest
from datetime import date
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient
from django.contrib.auth import get_user_model

from apps.designacao.models.cessacao import Cessacao
from apps.designacao.models.designacao import Designacao
from apps.designacao.models.insubsistencia import Insubsistencia

import secrets

User = get_user_model()


@pytest.fixture
def auth_client(db):
    password = secrets.token_urlsafe(16)
    user = User.objects.create_user(username="testuser", password=password)
    client = APIClient()
    client.force_authenticate(user=user)
    return client


@pytest.fixture
def designacao(db):
    return Designacao.objects.create(
        dre_nome="DRE TESTE",
        unidade_proponente="Unidade Teste",
        codigo_hierarquico="123",
        indicado_nome_civil="João da Silva",
        indicado_nome_servidor="João da Silva",
        indicado_rf="1234567",
        indicado_vinculo=1,
        indicado_cargo_base="Professor",
        indicado_lotacao="Escola A",
        indicado_local_exercicio="Escola A",
        numero_portaria="123",
        ano_vigente="2024",
        sei_numero="123456789",
        data_inicio=date(2024, 1, 1),
        tipo_vaga=Designacao.TipoVaga.VAGO,
        cargo_vaga=Designacao.CargoVaga.DIRETOR,
    )


@pytest.fixture
def insubsistencia(db, designacao):
    return Insubsistencia.objects.create(
        designacao=designacao,
        numero_portaria="456",
        ano_vigente="2024",
        sei_numero="88888",
        doc="DOE",
        observacoes="Observacao teste",
    )



@pytest.fixture
def cessacao(db, designacao):
    return Cessacao.objects.create(
        designacao=designacao,
        numero_portaria="12345",
        ano_vigente="2024",
        sei_numero="999999",
        doc="DOE",
        data_designacao="2024-03-10"
    )



class TestInsubsistenciaViewSet:
    @pytest.mark.django_db
    def test_create_insubsistencia_designacao(self, auth_client, designacao):
        url = reverse("designacao:insubsistencias")
        payload = {
            "designacao": designacao.id,
            "numero_portaria": "12345",
            "ano_vigente": "2024",
            "sei_numero": "999999",
            "doc": "DOE",
            "observacoes": "Criada via teste",
            "tipo_insubsistencia": "designacao",
        }
        response = auth_client.post(url, data=payload, format="json")
        assert response.status_code == status.HTTP_201_CREATED
 
    @pytest.mark.django_db
    def test_create_insubsistencia_de_cessacao_sem_cessacao(self, auth_client,designacao):
        url = reverse("designacao:insubsistencias")
        payload = {
            "designacao": designacao.id,
            "numero_portaria": "12345",
            "ano_vigente": "2024",
            "sei_numero": "999999",
            "doc": "DOE",
            "observacoes": "Criada via teste",
            "tipo_insubsistencia": "cessacao",
        }
        response = auth_client.post(url, data=payload, format="json")
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    @pytest.mark.django_db
    def test_create_insubsistencia_de_sem_tipo(self, auth_client,designacao):
        url = reverse("designacao:insubsistencias")
        payload = {
            "designacao": designacao.id,
            "numero_portaria": "12345",
            "ano_vigente": "2024",
            "sei_numero": "999999",
            "doc": "DOE",
            "observacoes": "Criada via teste",
        }
        response = auth_client.post(url, data=payload, format="json")
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    @pytest.mark.django_db
    def test_create_insubsistencia_cessacao(self, auth_client, cessacao, designacao):
        url = reverse("designacao:insubsistencias")
        payload = {
            "designacao": designacao.id,
            "numero_portaria": "12345",
            "ano_vigente": "2024",
            "sei_numero": "999999",
            "doc": "DOE",
            "observacoes": "Criada via teste",
            "tipo_insubsistencia": "cessacao",
        }
        response = auth_client.post(url, data=payload, format="json")
        assert response.status_code == status.HTTP_201_CREATED

    @pytest.mark.django_db
    def test_list_insubsistencias(self, auth_client, insubsistencia):
        url = reverse("designacao:insubsistencias")
        response = auth_client.get(url)
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data) >= 1

    @pytest.mark.django_db
    def test_retrieve_insubsistencia(self, auth_client, insubsistencia):
        url = reverse("designacao:insubsistencia-detail", args=[insubsistencia.id])
        response = auth_client.get(url)
        assert response.status_code == status.HTTP_200_OK
        assert response.data["id"] == insubsistencia.id

    @pytest.mark.django_db
    def test_nao_lista_insubsistencias_deletadas(self, auth_client, insubsistencia):
        insubsistencia.is_deleted = True
        insubsistencia.save()

        url = reverse("designacao:insubsistencias")
        response = auth_client.get(url)
        assert response.status_code == status.HTTP_200_OK

        data_list = response.data
        if isinstance(data_list, dict):
            data_list = [data_list]

        ids = [item["id"] for item in data_list if "id" in item]
        assert insubsistencia.id not in ids
