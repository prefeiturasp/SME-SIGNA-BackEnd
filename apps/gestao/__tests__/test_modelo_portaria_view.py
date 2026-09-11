"""Testes para a view de modelos de portaria."""

import secrets
from datetime import timedelta

import pytest
from django.contrib.auth import get_user_model
from django.urls import reverse
from django.utils import timezone
from rest_framework.test import APIClient

from apps.designacao.models.ato_administrativo import AtoAdministrativo
from apps.gestao.__tests__.factories import criar_modelo_portaria
from apps.gestao.models.modelo_portaria import ModeloPortaria

User = get_user_model()


@pytest.fixture
def auth_client(db):
    """Método auth client."""
    password = secrets.token_urlsafe(16)
    user = User.objects.create_user(username="test_gestao", password=password)
    client = APIClient()
    client.force_authenticate(user=user)
    return client


@pytest.mark.django_db
def test_list_exige_autenticacao():
    """Verifica que a listagem exige autenticação."""
    url = reverse("gestao:modelos-portaria")
    response = APIClient().get(url)

    assert response.status_code == 401


@pytest.mark.django_db
def test_list_retorna_modelos_paginados(auth_client):
    """Verifica que a listagem retorna os modelos cadastrados paginados."""
    criar_modelo_portaria(nome_modelo="Modelo 1")
    criar_modelo_portaria(nome_modelo="Modelo 2")

    url = reverse("gestao:modelos-portaria")
    response = auth_client.get(url)

    assert response.status_code == 200
    assert response.data["count"] == 2
    assert len(response.data["results"]) == 2


@pytest.mark.django_db
def test_list_retorna_modelos_ordenados_por_criado_em_decrescente(auth_client):
    """Verifica que a listagem retorna os modelos mais recentes primeiro."""
    mais_antigo = criar_modelo_portaria(nome_modelo="Modelo A")
    mais_novo = criar_modelo_portaria(nome_modelo="Modelo B")

    agora = timezone.now()
    ModeloPortaria.objects.filter(pk=mais_antigo.pk).update(
        criado_em=agora - timedelta(days=1)
    )
    ModeloPortaria.objects.filter(pk=mais_novo.pk).update(criado_em=agora)

    url = reverse("gestao:modelos-portaria")
    response = auth_client.get(url)

    assert response.status_code == 200
    nomes = [item["nome_modelo"] for item in response.data["results"]]
    assert nomes == ["Modelo B", "Modelo A"]


@pytest.mark.django_db
def test_list_retorna_tipo_de_ato_concatenado_com_tipo_ato_pai(auth_client):
    """Verifica que a listagem retorna tipo_de_ato concatenado com o pai."""
    criar_modelo_portaria(
        nome_modelo="Insubsistência de apostila",
        tipo_portaria=AtoAdministrativo.Tipo.INSUBSISTENCIA,
        tipo_ato_pai=AtoAdministrativo.Tipo.APOSTILA,
    )
    criar_modelo_portaria(
        nome_modelo="Designação diretor de escola",
        tipo_portaria=AtoAdministrativo.Tipo.DESIGNACAO,
        tipo_ato_pai="",
    )

    url = reverse("gestao:modelos-portaria")
    response = auth_client.get(url)

    assert response.status_code == 200
    tipos_de_ato = {
        item["nome_modelo"]: item["tipo_de_ato"]
        for item in response.data["results"]
    }
    assert (
        tipos_de_ato["Insubsistência de apostila"]
        == "Insubsistência de Apostila"
    )
    assert tipos_de_ato["Designação diretor de escola"] == "Designação"


@pytest.mark.django_db
def test_list_aplica_filtro_por_nome_modelo(auth_client):
    """Verifica que a listagem aplica o filtro de nome do modelo."""
    criar_modelo_portaria(nome_modelo="Designação diretor de escola")
    criar_modelo_portaria(nome_modelo="Cessação diretor de escola")

    url = reverse("gestao:modelos-portaria")
    response = auth_client.get(url, {"nome_modelo": "designação"})

    assert response.status_code == 200
    assert response.data["count"] == 1
    assert (
        response.data["results"][0]["nome_modelo"]
        == "Designação diretor de escola"
    )


@pytest.mark.django_db
def test_create_modelo_portaria_com_sucesso(auth_client):
    """Verifica que a criação de um modelo de portaria retorna 201."""
    payload = {
        "tipo_portaria": AtoAdministrativo.Tipo.DESIGNACAO,
        "nome_modelo": "Designação diretor de escola",
        "tipo_cargo": ModeloPortaria.TipoCargo.CARGO_VAGO,
        "variaveis": [
            ModeloPortaria.Variavel.NOME_SERVIDOR,
            ModeloPortaria.Variavel.NUMERO_RF,
        ],
        "texto_portaria": "O Secretário Municipal de Educação designa...",
    }

    url = reverse("gestao:modelos-portaria")
    response = auth_client.post(url, data=payload, format="json")

    assert response.status_code == 201
    assert response.data["nome_modelo"] == "Designação diretor de escola"
    assert response.data["status"] == ModeloPortaria.Status.ATIVO
    assert ModeloPortaria.objects.filter(
        nome_modelo="Designação diretor de escola"
    ).exists()


@pytest.mark.django_db
def test_create_modelo_portaria_sem_campo_obrigatorio_retorna_400(auth_client):
    """Verifica 400 quando falta um campo obrigatório no cadastro."""
    payload = {
        "tipo_portaria": AtoAdministrativo.Tipo.DESIGNACAO,
        "nome_modelo": "Designação diretor de escola",
    }

    url = reverse("gestao:modelos-portaria")
    response = auth_client.post(url, data=payload, format="json")

    assert response.status_code == 400


@pytest.mark.django_db
def test_retrieve_retorna_modelo_portaria(auth_client):
    """Verifica que o detalhe retorna os dados do modelo de portaria."""
    modelo = criar_modelo_portaria(nome_modelo="Designação diretor de escola")

    url = reverse("gestao:modelos-portaria-detail", kwargs={"pk": modelo.pk})
    response = auth_client.get(url)

    assert response.status_code == 200
    assert response.data["id"] == modelo.pk
    assert response.data["nome_modelo"] == "Designação diretor de escola"


@pytest.mark.django_db
def test_retrieve_inexistente_retorna_404(auth_client):
    """Verifica 404 ao consultar um modelo de portaria inexistente."""
    url = reverse("gestao:modelos-portaria-detail", kwargs={"pk": 9999})
    response = auth_client.get(url)

    assert response.status_code == 404


@pytest.mark.django_db
def test_patch_nao_esta_disponivel(auth_client):
    """Verifica que o PATCH foi removido e retorna 405."""
    modelo = criar_modelo_portaria(
        nome_modelo="Designação diretor de escola",
        status=ModeloPortaria.Status.ATIVO,
    )

    payload = {
        "nome_modelo": "Designação diretor de escola municipal",
        "status": ModeloPortaria.Status.INATIVO,
    }

    url = reverse("gestao:modelos-portaria-detail", kwargs={"pk": modelo.pk})
    response = auth_client.patch(url, data=payload, format="json")

    assert response.status_code == 405
    modelo.refresh_from_db()
    assert modelo.nome_modelo == "Designação diretor de escola"
    assert modelo.status == ModeloPortaria.Status.ATIVO


@pytest.mark.django_db
def test_patch_sem_autenticacao_retorna_401():
    """Verifica que o PATCH sem autenticação retorna 401, não 405."""
    modelo = criar_modelo_portaria()

    url = reverse("gestao:modelos-portaria-detail", kwargs={"pk": modelo.pk})
    response = APIClient().patch(
        url, data={"nome_modelo": "Novo"}, format="json"
    )

    assert response.status_code == 401


@pytest.mark.django_db
def test_variaveis_retorna_todas_as_opcoes(auth_client):
    """Verifica que o endpoint de variáveis retorna todas as opções."""
    url = reverse("gestao:modelos-portaria-variaveis")
    response = auth_client.get(url)

    assert response.status_code == 200
    assert len(response.data) == len(ModeloPortaria.Variavel.choices)
    assert {
        "value": "NOME_SERVIDOR",
        "display_name": "Nome do servidor",
    } in response.data


@pytest.mark.django_db
def test_variaveis_exige_autenticacao():
    """Verifica que o endpoint de variáveis exige autenticação."""
    url = reverse("gestao:modelos-portaria-variaveis")
    response = APIClient().get(url)

    assert response.status_code == 401
