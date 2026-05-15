import secrets
from datetime import date

import pytest
from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient

from apps.designacao.models import Cessacao, Designacao

User = get_user_model()


@pytest.fixture
def auth_client(db):
    """Cria um usuário e retorna um cliente autenticado."""
    password = secrets.token_urlsafe(16)
    user = User.objects.create_user(username="testuser", password=password)
    client = APIClient()
    client.force_authenticate(user=user)
    return client


@pytest.fixture
def designacao(db):
    """Factory simples de Designacao."""
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
def cessacao(db, designacao):
    """Factory simples de Cessacao."""
    return Cessacao.objects.create(
        designacao=designacao,
        numero_portaria="456",
        ano_vigente="2024",
        sei_numero="88888",
        a_pedido=True,
        data_designacao="2024-02-01",
    )


class TestCessacaoViewSet:

    def _payload(self, designacao_id):
        return {
            "designacao": designacao_id,
            "numero_portaria": "999",
            "ano_vigente": "2024",
            "sei_numero": "123456",
        }

    @pytest.mark.django_db
    def test_create_cessacao(self, auth_client, designacao):
        url = reverse("designacao:cessacoes")
        payload = {
            "designacao": designacao.id,
            "numero_portaria": "12345",
            "ano_vigente": "2024",
            "sei_numero": "999999",
            "a_pedido": True,
            "data_designacao": "2024-03-10",
        }
        response = auth_client.post(url, data=payload, format="json")
        print(response.data)
        assert response.status_code == 201

    def test_list_cessacoes(self, auth_client, cessacao):
        url = reverse("designacao:cessacoes")
        response = auth_client.get(url)
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data) >= 1

    def test_retrieve_cessacao(self, auth_client, cessacao):
        url = reverse("designacao:cessacao-detail", args=[cessacao.id])
        response = auth_client.get(url)
        assert response.status_code == status.HTTP_200_OK
        assert response.data["id"] == cessacao.id

    def test_delete_soft_delete(self, auth_client, cessacao):
        url = reverse("designacao:cessacao-detail", args=[cessacao.id])
        response = auth_client.delete(url)
        assert response.status_code == status.HTTP_204_NO_CONTENT
        # Confirma soft delete
        cessacao.refresh_from_db()
        assert cessacao.is_deleted is True

    @pytest.mark.django_db
    def test_nao_lista_cessacoes_deletadas(self, auth_client, cessacao):
        cessacao.is_deleted = True
        cessacao.save()

        url = reverse("designacao:cessacoes")
        response = auth_client.get(url)  # aqui auth_client é o fixture, funciona
        assert response.status_code == status.HTTP_200_OK

        data_list = response.data
        if isinstance(data_list, dict):
            data_list = [data_list]

        ids = [c["id"] for c in data_list if "id" in c]
        assert cessacao.id not in ids
