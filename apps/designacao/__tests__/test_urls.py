"""Testes das rotas nomeadas do app de designação."""

import pytest
from django.urls import resolve, reverse

ROTAS = [
    ("servidor", "/api/designacao/servidor", None),
    ("textos-sei-preview", "/api/designacao/textos-sei/preview/", None),
    ("unidade", "/api/designacao/unidade/", None),
    ("unidade-cargos", "/api/designacao/unidade/cargos/", None),
    ("unidade-cadastradas", "/api/designacao/unidade/cadastradas/", None),
    ("designacoes", "/api/designacao/designacoes/", None),
    ("impedimentos", "/api/designacao/designacoes/impedimentos/", None),
    ("designacao-detail", "/api/designacao/designacoes/10/", {"pk": 10}),
    (
        "cargos-designacoes",
        "/api/designacao/designacoes/cargos-designacoes/",
        None,
    ),
    (
        "cargos-base-pareados",
        "/api/designacao/designacoes/cargos-base-pareados/",
        None,
    ),
    (
        "cargos-sobrepostos-pareados",
        "/api/designacao/designacoes/cargos-sobrepostos-pareados/",
        None,
    ),
    (
        "designacao-buscar-por-portaria",
        "/api/designacao/designacoes/buscar-por-portaria/",
        None,
    ),
    (
        "historico-de-designacoes",
        "/api/designacao/historico-de-designacoes/019453/",
        {"codigo_ue": "019453"},
    ),
    ("cessacoes", "/api/designacao/cessacoes/", None),
    ("cessacao-detail", "/api/designacao/cessacoes/20/", {"pk": 20}),
    (
        "cessacao-buscar-por-portaria",
        "/api/designacao/cessacoes/buscar-por-portaria/",
        None,
    ),
    ("apostilas", "/api/designacao/apostilas/", None),
    ("apostila-detail", "/api/designacao/apostilas/30/", {"pk": 30}),
    ("insubsistencias", "/api/designacao/insubsistencias/", None),
    (
        "insubsistencia-detail",
        "/api/designacao/insubsistencias/40/",
        {"pk": 40},
    ),
    (
        "insubsistencia-buscar-por-portaria",
        "/api/designacao/insubsistencias/buscar-por-portaria/",
        None,
    ),
    ("portarias", "/api/designacao/portarias/", None),
    (
        "portarias-atualizar-data-publicacao",
        "/api/designacao/portarias/atualizar-data-publicacao/",
        None,
    ),
    ("portarias-lauda", "/api/designacao/portarias/lauda/", None),
    ("atos-administrativos", "/api/designacao/atos-administrativos/", None),
]


@pytest.mark.parametrize(("nome", "caminho", "kwargs"), ROTAS)
def test_rota_resolve_o_caminho_esperado(nome, caminho, kwargs):
    assert reverse(f"designacao:{nome}", kwargs=kwargs) == caminho

    resolvida = resolve(caminho)
    assert resolvida.url_name == nome
    assert resolvida.namespace == "designacao"
