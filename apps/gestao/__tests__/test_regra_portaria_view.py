"""Testes para a view de regras de portaria."""

import secrets

import pytest
from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework.test import APIClient

from apps.gestao.__tests__.factories import criar_regra_portaria
from apps.gestao.models.regra_portaria import RegraPortaria

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
    url = reverse("gestao:regras-portaria")
    response = APIClient().get(url)

    assert response.status_code == 401


@pytest.mark.django_db
def test_list_retorna_regras_paginadas(auth_client):
    """Verifica que a listagem retorna as regras cadastradas paginadas."""
    criar_regra_portaria(codigo_cargo_eol="3360")
    criar_regra_portaria(codigo_cargo_eol="3182")

    url = reverse("gestao:regras-portaria")
    response = auth_client.get(url)

    assert response.status_code == 200
    assert response.data["count"] == 2
    assert len(response.data["results"]) == 2


@pytest.mark.django_db
def test_list_aplica_filtro_por_cargo(auth_client):
    """Verifica que a listagem aplica o filtro de cargo."""
    criar_regra_portaria(
        codigo_cargo_eol="3360", descricao_resumida_cargo="Diretor"
    )
    criar_regra_portaria(
        codigo_cargo_eol="3182", descricao_resumida_cargo="Secretário"
    )

    url = reverse("gestao:regras-portaria")
    response = auth_client.get(url, {"cargo": "diretor"})

    assert response.status_code == 200
    assert response.data["count"] == 1
    assert response.data["results"][0]["codigo_cargo_eol"] == "3360"


@pytest.mark.django_db
def test_create_regra_portaria_com_sucesso(auth_client):
    """Verifica que a criação de uma regra de portaria retorna 201."""
    payload = {
        "descricao_resumida_cargo": "Diretor",
        "descricao_completa_cargo": "Diretor de escola",
        "codigo_cargo_eol": "3360",
        "tipo_modulo": RegraPortaria.TipoModulo.TURMAS,
        "texto_publicacao": "Designar o(a) servidor(a)...",
        "emitente": RegraPortaria.Emitente.SECRETARIO_MUNICIPAL_EDUCACAO,
    }

    url = reverse("gestao:regras-portaria")
    response = auth_client.post(url, data=payload, format="json")

    assert response.status_code == 201
    assert response.data["codigo_cargo_eol"] == "3360"
    assert response.data["status"] == RegraPortaria.Status.ATIVO
    assert RegraPortaria.objects.filter(codigo_cargo_eol="3360").exists()


@pytest.mark.django_db
def test_create_regra_portaria_duplicada_retorna_400(auth_client):
    """Verifica 400 ao cadastrar regra com código EOL já existente."""
    criar_regra_portaria(codigo_cargo_eol="3360")

    payload = {
        "descricao_resumida_cargo": "Diretor",
        "descricao_completa_cargo": "Diretor de escola",
        "codigo_cargo_eol": "3360",
        "tipo_modulo": RegraPortaria.TipoModulo.TURMAS,
        "texto_publicacao": "Designar o(a) servidor(a)...",
        "emitente": RegraPortaria.Emitente.SECRETARIO_MUNICIPAL_EDUCACAO,
    }

    url = reverse("gestao:regras-portaria")
    response = auth_client.post(url, data=payload, format="json")

    assert response.status_code == 400
    assert "codigo_cargo_eol" in response.data


@pytest.mark.django_db
def test_create_regra_portaria_sem_campo_obrigatorio_retorna_400(auth_client):
    """Verifica 400 quando falta um campo obrigatório no cadastro."""
    payload = {
        "descricao_resumida_cargo": "Diretor",
        "codigo_cargo_eol": "3360",
    }

    url = reverse("gestao:regras-portaria")
    response = auth_client.post(url, data=payload, format="json")

    assert response.status_code == 400


@pytest.mark.django_db
def test_retrieve_retorna_regra_portaria(auth_client):
    """Verifica que o detalhe retorna os dados da regra de portaria."""
    regra = criar_regra_portaria(codigo_cargo_eol="3360")

    url = reverse("gestao:regras-portaria-detail", kwargs={"pk": regra.pk})
    response = auth_client.get(url)

    assert response.status_code == 200
    assert response.data["id"] == regra.pk
    assert response.data["codigo_cargo_eol"] == "3360"


@pytest.mark.django_db
def test_retrieve_inexistente_retorna_404(auth_client):
    """Verifica 404 ao consultar uma regra de portaria inexistente."""
    url = reverse("gestao:regras-portaria-detail", kwargs={"pk": 9999})
    response = auth_client.get(url)

    assert response.status_code == 404


@pytest.mark.django_db
def test_retrieve_exige_autenticacao():
    """Verifica que o detalhe exige autenticação."""
    regra = criar_regra_portaria(codigo_cargo_eol="3360")

    url = reverse("gestao:regras-portaria-detail", kwargs={"pk": regra.pk})
    response = APIClient().get(url)

    assert response.status_code == 401


@pytest.mark.django_db
def test_partial_update_altera_campos_editaveis(auth_client):
    """Verifica que o PATCH altera os campos permitidos."""
    regra = criar_regra_portaria(
        codigo_cargo_eol="3360",
        descricao_resumida_cargo="Diretor",
        tipo_modulo=RegraPortaria.TipoModulo.TURMAS,
        status=RegraPortaria.Status.ATIVO,
        utilizar_numero_sei=False,
    )

    payload = {
        "descricao_resumida_cargo": "Diretor de Escola Municipal",
        "tipo_modulo": RegraPortaria.TipoModulo.NENHUM,
        "status": RegraPortaria.Status.INATIVO,
        "utilizar_numero_sei": True,
        "normas": "Lei nº 123",
    }

    url = reverse("gestao:regras-portaria-detail", kwargs={"pk": regra.pk})
    response = auth_client.patch(url, data=payload, format="json")

    assert response.status_code == 200
    regra.refresh_from_db()
    assert regra.descricao_resumida_cargo == "Diretor de Escola Municipal"
    assert regra.tipo_modulo == RegraPortaria.TipoModulo.NENHUM
    assert regra.status == RegraPortaria.Status.INATIVO
    assert regra.utilizar_numero_sei is True
    assert regra.normas == "Lei nº 123"


@pytest.mark.django_db
def test_partial_update_exige_autenticacao():
    """Verifica que o PATCH exige autenticação."""
    regra = criar_regra_portaria(codigo_cargo_eol="3360")

    url = reverse("gestao:regras-portaria-detail", kwargs={"pk": regra.pk})
    response = APIClient().patch(
        url, data={"descricao_resumida_cargo": "Novo"}, format="json"
    )

    assert response.status_code == 401


@pytest.mark.django_db
def test_partial_update_inexistente_retorna_404(auth_client):
    """Verifica 404 ao editar uma regra de portaria inexistente."""
    url = reverse("gestao:regras-portaria-detail", kwargs={"pk": 9999})
    response = auth_client.patch(
        url, data={"descricao_resumida_cargo": "Novo"}, format="json"
    )

    assert response.status_code == 404
