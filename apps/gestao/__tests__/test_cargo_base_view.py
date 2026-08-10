"""Testes para a view de cargos base."""

import secrets

import pytest
from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework.test import APIClient

from apps.gestao.__tests__.factories import criar_cargo_base
from apps.gestao.models.cargo_base import CargoBase

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
    url = reverse("gestao:cargos-base")
    response = APIClient().get(url)

    assert response.status_code == 401


@pytest.mark.django_db
def test_list_retorna_cargos_paginados(auth_client):
    """Verifica que a listagem retorna os cargos cadastrados paginados."""
    criar_cargo_base(codigo_cargo="3360")
    criar_cargo_base(codigo_cargo="3182")

    url = reverse("gestao:cargos-base")
    response = auth_client.get(url)

    assert response.status_code == 200
    assert response.data["count"] == 2
    assert len(response.data["results"]) == 2


@pytest.mark.django_db
def test_list_retorna_vazio_quando_nao_ha_correspondencia(auth_client):
    """Verifica que a listagem retorna vazio quando o filtro não casa."""
    criar_cargo_base(
        codigo_cargo="3360", grupamento=CargoBase.Grupamento.GESTORES_EDUCACAO
    )

    url = reverse("gestao:cargos-base")
    response = auth_client.get(url, {"grupamento": "DOCENTES"})

    assert response.status_code == 200
    assert response.data["count"] == 0
    assert response.data["results"] == []


@pytest.mark.django_db
def test_list_aplica_filtro_por_descricao_resumida(auth_client):
    """Verifica que a listagem aplica o filtro de descrição resumida."""
    criar_cargo_base(
        codigo_cargo="3360", descricao_resumida="Diretor de Escola"
    )
    criar_cargo_base(
        codigo_cargo="3182", descricao_resumida="Secretário de Escola"
    )

    url = reverse("gestao:cargos-base")
    response = auth_client.get(url, {"descricao_resumida": "diretor"})

    assert response.status_code == 200
    assert response.data["count"] == 1
    assert response.data["results"][0]["codigo_cargo"] == "3360"


@pytest.mark.django_db
def test_create_cargo_base_com_sucesso(auth_client):
    """Verifica que a criação de um cargo base retorna 201 com os dados."""
    payload = {
        "codigo_cargo": "3352",
        "descricao_completa": "SUPERVISOR ESCOLAR",
        "descricao_resumida": "Supervisor Escolar",
        "grupamento": CargoBase.Grupamento.GESTORES_EDUCACAO,
        "situacao_funcional": CargoBase.SituacaoFuncional.EFETIVO,
    }

    url = reverse("gestao:cargos-base")
    response = auth_client.post(url, data=payload, format="json")

    assert response.status_code == 201
    assert response.data["codigo_cargo"] == "3352"
    assert response.data["status"] == CargoBase.Status.ATIVO
    assert CargoBase.objects.filter(codigo_cargo="3352").exists()


@pytest.mark.django_db
def test_create_cargo_base_duplicado_retorna_400(auth_client):
    """Verifica 400 ao tentar cadastrar cargo com código já existente."""
    criar_cargo_base(codigo_cargo="3360")

    payload = {
        "codigo_cargo": "3360",
        "descricao_completa": "DIRETOR DE ESCOLA",
        "descricao_resumida": "Diretor",
        "grupamento": CargoBase.Grupamento.GESTORES_EDUCACAO,
        "situacao_funcional": CargoBase.SituacaoFuncional.EFETIVO,
    }

    url = reverse("gestao:cargos-base")
    response = auth_client.post(url, data=payload, format="json")

    assert response.status_code == 400
    assert "codigo_cargo" in response.data


@pytest.mark.django_db
def test_create_cargo_base_sem_campo_obrigatorio_retorna_400(auth_client):
    """Verifica 400 quando falta um campo obrigatório no cadastro."""
    payload = {
        "codigo_cargo": "3352",
        "descricao_completa": "SUPERVISOR ESCOLAR",
    }

    url = reverse("gestao:cargos-base")
    response = auth_client.post(url, data=payload, format="json")

    assert response.status_code == 400


@pytest.mark.django_db
def test_cargos_eol_retorna_lista_da_sme(auth_client, monkeypatch):
    """Verifica que o proxy de cargos do EOL repassa a lista da SME."""
    cargos_mock = [
        {"codigoCargo": "3360", "descricaoCargo": "DIRETOR DE ESCOLA"},
    ]
    monkeypatch.setattr(
        "apps.gestao.api.views.cargo_base_view.SmeIntegracaoService.buscar_cargos",
        lambda: cargos_mock,
    )

    url = reverse("gestao:cargos-eol")
    response = auth_client.get(url)

    assert response.status_code == 200
    assert response.data == cargos_mock


@pytest.mark.django_db
def test_cargos_eol_erro_sme_retorna_400(auth_client, monkeypatch):
    """Verifica que erro de integração no proxy de cargos retorna 400."""
    from apps.helpers.exceptions import SmeIntegracaoError

    def _levanta_erro():
        raise SmeIntegracaoError("Erro ao consultar cargos do servidor")

    monkeypatch.setattr(
        "apps.gestao.api.views.cargo_base_view.SmeIntegracaoService.buscar_cargos",
        _levanta_erro,
    )

    url = reverse("gestao:cargos-eol")
    response = auth_client.get(url)

    assert response.status_code == 400
    assert response.data["detail"] == "Erro ao consultar cargos do servidor"


@pytest.mark.django_db
def test_cargos_eol_erro_inesperado_retorna_500(auth_client, monkeypatch):
    """Verifica que um erro inesperado no proxy de cargos retorna 500."""

    def _levanta_erro():
        raise RuntimeError("falha inesperada")

    monkeypatch.setattr(
        "apps.gestao.api.views.cargo_base_view.SmeIntegracaoService.buscar_cargos",
        _levanta_erro,
    )

    url = reverse("gestao:cargos-eol")
    response = auth_client.get(url)

    assert response.status_code == 500
    assert response.data["detail"] == "Erro interno do servidor"


@pytest.mark.django_db
def test_cargos_eol_exige_autenticacao():
    """Verifica que o proxy de cargos do EOL exige autenticação."""
    url = reverse("gestao:cargos-eol")
    response = APIClient().get(url)

    assert response.status_code == 401


@pytest.mark.django_db
def test_retrieve_retorna_cargo_base(auth_client):
    """Verifica que o detalhe retorna os dados do cargo base."""
    cargo = criar_cargo_base(codigo_cargo="3360")

    url = reverse("gestao:cargos-base-detail", kwargs={"pk": cargo.pk})
    response = auth_client.get(url)

    assert response.status_code == 200
    assert response.data["id"] == cargo.pk
    assert response.data["codigo_cargo"] == "3360"


@pytest.mark.django_db
def test_retrieve_inexistente_retorna_404(auth_client):
    """Verifica 404 ao consultar um cargo base inexistente."""
    url = reverse("gestao:cargos-base-detail", kwargs={"pk": 9999})
    response = auth_client.get(url)

    assert response.status_code == 404


@pytest.mark.django_db
def test_retrieve_exige_autenticacao():
    """Verifica que o detalhe exige autenticação."""
    cargo = criar_cargo_base(codigo_cargo="3360")

    url = reverse("gestao:cargos-base-detail", kwargs={"pk": cargo.pk})
    response = APIClient().get(url)

    assert response.status_code == 401


@pytest.mark.django_db
def test_partial_update_altera_campos_editaveis(auth_client):
    """Verifica que o PATCH altera os campos permitidos."""
    cargo = criar_cargo_base(
        codigo_cargo="3360",
        descricao_resumida="Diretor de Escola",
        grupamento=CargoBase.Grupamento.GESTORES_EDUCACAO,
        situacao_funcional=CargoBase.SituacaoFuncional.EFETIVO,
        status=CargoBase.Status.ATIVO,
    )

    payload = {
        "descricao_resumida": "Diretor de Escola Municipal",
        "grupamento": CargoBase.Grupamento.APOIO_EDUCACAO,
        "situacao_funcional": CargoBase.SituacaoFuncional.COMISSIONADO,
        "status": CargoBase.Status.INATIVO,
        "utilizado_para_funcoes": False,
        "utilizado_para_designacoes": False,
        "utilizado_para_ste": False,
        "utilizado_para_permutas": True,
        "cargo_base_ficticio": True,
    }

    url = reverse("gestao:cargos-base-detail", kwargs={"pk": cargo.pk})
    response = auth_client.patch(url, data=payload, format="json")

    assert response.status_code == 200
    cargo.refresh_from_db()
    assert cargo.descricao_resumida == "Diretor de Escola Municipal"
    assert cargo.grupamento == CargoBase.Grupamento.APOIO_EDUCACAO
    assert cargo.situacao_funcional == CargoBase.SituacaoFuncional.COMISSIONADO
    assert cargo.status == CargoBase.Status.INATIVO
    assert cargo.utilizado_para_funcoes is False
    assert cargo.utilizado_para_designacoes is False
    assert cargo.utilizado_para_ste is False
    assert cargo.utilizado_para_permutas is True
    assert cargo.cargo_base_ficticio is True


@pytest.mark.django_db
def test_partial_update_ignora_codigo_cargo_e_descricao_completa(auth_client):
    """Verifica que o PATCH não altera código e descrição completa."""
    cargo = criar_cargo_base(
        codigo_cargo="3360",
        descricao_completa="DIRETOR DE ESCOLA MUNICIPAL",
    )

    payload = {
        "codigo_cargo": "9999",
        "descricao_completa": "OUTRO CARGO QUALQUER",
        "descricao_resumida": "Diretor de Escola Municipal",
    }

    url = reverse("gestao:cargos-base-detail", kwargs={"pk": cargo.pk})
    response = auth_client.patch(url, data=payload, format="json")

    assert response.status_code == 200
    cargo.refresh_from_db()
    assert cargo.codigo_cargo == "3360"
    assert cargo.descricao_completa == "DIRETOR DE ESCOLA MUNICIPAL"
    assert cargo.descricao_resumida == "Diretor de Escola Municipal"


@pytest.mark.django_db
def test_partial_update_exige_autenticacao():
    """Verifica que o PATCH exige autenticação."""
    cargo = criar_cargo_base(codigo_cargo="3360")

    url = reverse("gestao:cargos-base-detail", kwargs={"pk": cargo.pk})
    response = APIClient().patch(
        url, data={"descricao_resumida": "Novo"}, format="json"
    )

    assert response.status_code == 401
