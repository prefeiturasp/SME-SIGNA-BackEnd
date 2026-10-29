"""Testes da contagem de designações vigentes por cargo."""

import datetime

import pytest
from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework.test import APIClient
from rest_framework_simplejwt.tokens import AccessToken

from apps.designacao.__tests__.factories import (
    criar_ato_apostila,
    criar_ato_cessacao,
    criar_ato_designacao,
    criar_ato_insubsistencia,
)
from apps.designacao.services.designacao_service import DesignacaoService
from apps.gestao.models.cargo_base import CargoBase

pytestmark = pytest.mark.django_db

TODOS = {"codigoCargo": None, "nomeCargo": "Todos os cargos"}


def _cargos_do_cadastro() -> list[dict]:
    """Cargos ativos utilizados para designação, na ordem do painel."""
    return [
        {
            "codigoCargo": int(cargo.codigo_cargo),
            "nomeCargo": cargo.descricao_completa,
        }
        for cargo in CargoBase.objects.filter(
            status=CargoBase.Status.ATIVO,
            utilizado_para_designacoes=True,
        ).order_by("descricao_resumida")
    ]


@pytest.fixture
def client():
    user = get_user_model().objects.create_user(username="contagem-cargos")
    client = APIClient()
    client.credentials(
        HTTP_AUTHORIZATION=f"Bearer {AccessToken.for_user(user)}"
    )
    return client


def test_exige_autenticacao():
    response = APIClient().get(reverse("designacao:cargos-designacoes"))
    assert response.status_code == 401


def test_rejeita_token_invalido():
    client = APIClient()
    client.credentials(HTTP_AUTHORIZATION="Bearer invalido")
    response = client.get(
        reverse("designacao:cargos-designacoes"), {"ue": "019453"}
    )
    assert response.status_code == 401


def test_retorna_total_e_cargos_do_cadastro_sem_designacoes(client):
    response = client.get(
        reverse("designacao:cargos-designacoes"), {"ue": "019453"}
    )
    assert response.status_code == 200
    assert response.data == [
        {**cargo, "quantidade_designacoes": 0}
        for cargo in [TODOS, *_cargos_do_cadastro()]
    ]


def test_agrupa_por_cargo_da_vaga_sem_duplicar_designacoes(client):
    cargos = _cargos_do_cadastro()
    for quantidade, cargo in enumerate(cargos, start=1):
        for _ in range(quantidade):
            ato = criar_ato_designacao(
                ue="019453",
                cargo_vaga=cargo["codigoCargo"],
                indicado_codigo_cargo_base=9999,
            )
            criar_ato_apostila(ato)
            criar_ato_apostila(ato)
    # Códigos ausentes do cadastro entram só no total.
    criar_ato_designacao(ue="019453", cargo_vaga=9999)
    criar_ato_designacao(ue="019453", cargo_vaga=None)

    response = client.get(
        reverse("designacao:cargos-designacoes"), {"ue": "019453"}
    )

    total = sum(range(1, len(cargos) + 1)) + 2
    assert response.status_code == 200
    assert response.data[0] == {**TODOS, "quantidade_designacoes": total}
    assert response.data[1:] == [
        {**cargo, "quantidade_designacoes": quantidade}
        for quantidade, cargo in enumerate(cargos, start=1)
    ]


def test_atos_relacionados_nao_aumentam_quantidade_de_designacoes(client):
    designacao = criar_ato_designacao(ue="019453", cargo_vaga=3360)
    criar_ato_apostila(designacao)
    criar_ato_apostila(designacao)
    cessacao = criar_ato_cessacao(designacao)
    criar_ato_insubsistencia(cessacao)
    cessacao.ativo = False
    cessacao.save()

    response = client.get(
        reverse("designacao:cargos-designacoes"), {"ue": "019453"}
    )

    assert response.status_code == 200
    assert response.data[0]["quantidade_designacoes"] == 1
    diretor = next(c for c in response.data if c["codigoCargo"] == 3360)
    assert diretor["quantidade_designacoes"] == 1


@pytest.mark.parametrize(
    ("fim", "ativo", "cessacao_ativa", "inicio_futuro", "vigente"),
    [
        (None, True, None, False, 1),
        (0, True, None, False, 1),
        (1, True, None, False, 1),
        (-1, True, None, False, 0),
        (None, False, None, False, 0),
        (None, True, True, False, 0),
        (None, True, False, False, 1),
        (None, True, None, True, 1),
    ],
)
def test_conta_designacoes_independentemente_da_vigencia(
    fim,
    ativo,
    cessacao_ativa,
    inicio_futuro,
    vigente,
    django_assert_num_queries,
):
    hoje = datetime.datetime.now().date()
    ato = criar_ato_designacao(
        ue="019453",
        cargo_vaga=3360,
        data_inicio=hoje + datetime.timedelta(days=1 if inicio_futuro else -5),
        data_fim=(
            hoje + datetime.timedelta(days=fim) if fim is not None else None
        ),
    )
    ato.ativo = ativo
    ato.save()
    if cessacao_ativa is not None:
        cessacao = criar_ato_cessacao(ato)
        cessacao.ativo = cessacao_ativa
        cessacao.save()

    assert ato.esta_vigente == bool(vigente)
    with django_assert_num_queries(2):
        resultado = DesignacaoService.contar_designacoes_por_cargo("019453")
    diretor = next(
        cargo for cargo in resultado if cargo["codigoCargo"] == 3360
    )
    assert diretor["quantidade_designacoes"] == 1


@pytest.mark.parametrize("parametros", [{}, {"ue": ""}, {"ue": "   "}])
def test_ue_obrigatoria(client, parametros):
    criar_ato_designacao(ue="019453", cargo_vaga=3360)
    response = client.get(reverse("designacao:cargos-designacoes"), parametros)
    assert response.status_code == 400


@pytest.mark.parametrize("ue", ["019453", "19453"])
def test_conta_somente_designacoes_da_ue(client, ue):
    criar_ato_designacao(ue="019453", cargo_vaga=3360)
    criar_ato_designacao(ue="19453", cargo_vaga=3360)
    criar_ato_designacao(ue="099999", cargo_vaga=3360)
    criar_ato_designacao(ue="", cargo_vaga=3360)
    response = client.get(reverse("designacao:cargos-designacoes"), {"ue": ue})
    assert response.status_code == 200
    assert response.data[0]["quantidade_designacoes"] == 2
    diretor = next(c for c in response.data if c["codigoCargo"] == 3360)
    assert diretor["quantidade_designacoes"] == 2


def test_ue_sem_designacoes_retorna_zeros(client):
    criar_ato_designacao(ue="099999", cargo_vaga=3360)
    response = client.get(
        reverse("designacao:cargos-designacoes"), {"ue": "019453"}
    )
    assert response.status_code == 200
    assert all(c["quantidade_designacoes"] == 0 for c in response.data)


def test_exemplo_tres_coordenadores_e_dois_diretores(client):
    for cargo in (3379, 3379, 3379, 3360, 3360):
        criar_ato_designacao(ue="019453", cargo_vaga=cargo)

    response = client.get(
        reverse("designacao:cargos-designacoes"), {"ue": "019453"}
    )

    esperado = {cargo["codigoCargo"]: 0 for cargo in _cargos_do_cadastro()}
    esperado[None] = 5
    esperado[3379] = 3
    esperado[3360] = 2
    assert response.status_code == 200
    assert {
        item["codigoCargo"]: item["quantidade_designacoes"]
        for item in response.data
    } == esperado
