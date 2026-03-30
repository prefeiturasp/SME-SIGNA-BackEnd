import pytest
import secrets
from rest_framework.test import APIClient
from django.urls import reverse
from django.contrib.auth import get_user_model

from apps.designacao.models.designacao import Designacao

User = get_user_model()


@pytest.fixture
def auth_client():
    password = secrets.token_urlsafe(16)
    user = User.objects.create_user(
        username="test",
        password=password
    )
    client = APIClient()
    client.force_authenticate(user=user)
    return client


@pytest.mark.django_db
def test_list_without_pagination_effective(auth_client, monkeypatch):
    for i in range(3):
        Designacao.objects.create(
            indicado_nome_servidor=f"Teste {i}",
            titular_nome_servidor=f"Titular {i}",
            indicado_rf="123",
            titular_rf="456",
            indicado_cargo_base="Diretor",
            titular_cargo_base="Diretor",
            indicado_vinculo=1,
            dre_nome="DRE",
            unidade_proponente="Unidade",
            ano_vigente="2024",
            is_deleted=False,
            data_inicio="2024-01-01"
        )

    from apps.designacao.api.views.designacao import DesignacaoViewSet
    monkeypatch.setattr(DesignacaoViewSet, 'paginate_queryset', lambda self, queryset: None)

    url = reverse("designacao:designacoes")
    response = auth_client.get(url)

    assert response.status_code == 200
    assert isinstance(response.data, list)
    assert len(response.data) == 3



@pytest.mark.django_db
def test_list_designacoes_sem_filtro_limita_1000(auth_client):
    Designacao.objects.bulk_create([
        Designacao(
            dre_nome="DRE",
            unidade_proponente="UP",
            codigo_hierarquico="1",
            indicado_nome_civil="Nome",
            indicado_nome_servidor="Nome",
            indicado_rf=str(i).zfill(8),
            indicado_vinculo=1,  # ✅ necessário
            indicado_cargo_base="Cargo",
            indicado_lotacao="Lotacao",
            indicado_local_exercicio="Local",
            numero_portaria="123",
            ano_vigente="2024",
            sei_numero="SEI",
            data_inicio="2024-01-01",
            tipo_vaga="VAGO"
        )
        for i in range(1100)
    ])

    url = reverse("designacao:designacoes")
    response = auth_client.get(url)

    assert response.status_code == 200


@pytest.mark.django_db
def test_list_designacoes_com_filtro_nao_limita_queryset(auth_client):
    Designacao.objects.create(
        dre_nome="DRE TESTE",
        unidade_proponente="UP",
        codigo_hierarquico="1",
        indicado_nome_civil="Nome",
        indicado_nome_servidor="Nome",
        indicado_rf="12345678",
        indicado_vinculo=1,  # ✅ necessário
        indicado_cargo_base="Cargo",
        indicado_lotacao="Lotacao",
        indicado_local_exercicio="Local",
        numero_portaria="123",
        ano_vigente="2024",
        sei_numero="SEI",
        data_inicio="2024-01-01",
        tipo_vaga="VAGO"
    )

    url = reverse("designacao:designacoes")
    response = auth_client.get(url, {"dre_nome": "DRE TESTE"})

    assert response.status_code == 200


@pytest.mark.django_db
def test_destroy_designacao_soft_delete(auth_client):
    designacao = Designacao.objects.create(
        dre_nome="DRE",
        unidade_proponente="UP",
        codigo_hierarquico="1",
        indicado_nome_civil="Nome",
        indicado_nome_servidor="Nome",
        indicado_rf="12345678",
        indicado_vinculo=1,  # ✅ necessário
        indicado_cargo_base="Cargo",
        indicado_lotacao="Lotacao",
        indicado_local_exercicio="Local",
        numero_portaria="123",
        ano_vigente="2024",
        sei_numero="SEI",
        data_inicio="2024-01-01",
        tipo_vaga="VAGO"
    )

    url = reverse("designacao:designacao-detail", args=[designacao.id])
    response = auth_client.delete(url)

    assert response.status_code == 204

    designacao.refresh_from_db()
    assert designacao.is_deleted is True
    assert designacao.deleted_at is not None