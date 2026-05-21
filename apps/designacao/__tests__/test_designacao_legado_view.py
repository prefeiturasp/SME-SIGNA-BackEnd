import secrets

from django.contrib.auth import get_user_model
from django.urls import reverse

import pytest
from rest_framework.test import APIClient

from apps.designacao.__tests__.factories import criar_designacao_legado

User = get_user_model()


@pytest.fixture
def auth_client(db):
    password = secrets.token_urlsafe(16)
    user = User.objects.create_user(username="test_legado", password=password)
    client = APIClient()
    client.force_authenticate(user=user)
    return client


@pytest.mark.django_db
def test_list_designacoes_legado(auth_client):
    criar_designacao_legado()
    criar_designacao_legado(sei_numero="SEI-2", indicado_rf="7654321")

    url = reverse("designacao:designacoes")
    response = auth_client.get(url)

    assert response.status_code == 200
    assert response.data["count"] >= 2


@pytest.mark.django_db
def test_list_legado_no_pagination(auth_client):
    for i in range(3):
        criar_designacao_legado(
            sei_numero=f"SEI-{i}", indicado_rf=f"000000{i}"
        )

    url = reverse("designacao:designacoes")
    response = auth_client.get(url, {"no_pagination": "true"})

    assert response.status_code == 200
    assert isinstance(response.data, list)
    assert len(response.data) >= 3


@pytest.mark.django_db
def test_list_legado_nao_retorna_deletados(auth_client):
    d = criar_designacao_legado()
    d.is_deleted = True
    d.save()

    url = reverse("designacao:designacoes")
    response = auth_client.get(url)

    assert response.status_code == 200
    ids = [item["id"] for item in response.data.get("results", [])]
    assert d.id not in ids


@pytest.mark.django_db
def test_destroy_designacao_legado_soft_delete(auth_client):
    d = criar_designacao_legado()

    url = reverse("designacao:designacao-detail", args=[d.id])
    response = auth_client.delete(url)

    assert response.status_code == 204
    d.refresh_from_db()
    assert d.is_deleted is True


@pytest.mark.django_db
def test_retrieve_designacao_legado(auth_client):
    d = criar_designacao_legado()

    url = reverse("designacao:designacao-detail", args=[d.id])
    response = auth_client.get(url)

    assert response.status_code == 200
    assert response.data["id"] == d.id


@pytest.mark.django_db
def test_cargos_base_pareados_legado(auth_client):
    url = reverse("designacao:cargos-base-pareados")
    response = auth_client.get(url)

    assert response.status_code == 200
    assert isinstance(response.data, list)


@pytest.mark.django_db
def test_cargos_sobrepostos_pareados_legado(auth_client):
    url = reverse("designacao:cargos-sobrepostos-pareados")
    response = auth_client.get(url)

    assert response.status_code == 200
    assert isinstance(response.data, list)
