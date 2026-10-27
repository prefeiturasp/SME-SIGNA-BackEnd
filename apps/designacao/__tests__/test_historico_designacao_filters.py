"""Testes dos filtros do histórico de designações por unidade escolar.

Cobre os filtros `status_publicacao`, `periodo` (params `periodo_after` e
`periodo_before`) e `observacao`, tanto no ``FilterSet`` (unidade) quanto
no endpoint (integração).
"""

import datetime
import secrets

import pytest
from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework.test import APIClient

from apps.designacao.__tests__.factories import (
    criar_ato_apostila,
    criar_ato_cessacao,
    criar_ato_designacao,
    criar_ato_insubsistencia,
)
from apps.designacao.api.filters.historico_designacao_filter import (
    HistoricoDesignacaoFilter,
)
from apps.designacao.models.ato_administrativo import AtoAdministrativo
from apps.designacao.services.historico_designacao_service import (
    HistoricoDesignacaoService,
)

User = get_user_model()

UE = "019453"


@pytest.fixture
def auth_client(db):
    """Cliente autenticado para as requisições dos testes."""
    password = secrets.token_urlsafe(16)
    user = User.objects.create_user(username="test", password=password)
    client = APIClient()
    client.force_authenticate(user=user)
    return client


def _url(codigo_ue=UE):
    """Monta a URL do histórico para o código de UE informado."""
    return reverse(
        "designacao:historico-de-designacoes", kwargs={"codigo_ue": codigo_ue}
    )


def _designacoes():
    """Queryset base usado nos testes de unidade do filtro."""
    return AtoAdministrativo.objects.filter(
        tipo=AtoAdministrativo.Tipo.DESIGNACAO
    )


def _publicar(ato: AtoAdministrativo) -> AtoAdministrativo:
    """Marca a designação como publicada."""
    AtoAdministrativo.objects.filter(pk=ato.pk).update(
        status_publicacao=AtoAdministrativo.StatusPublicacao.PUBLICADO
    )
    ato.refresh_from_db()
    return ato


# ── status_publicacao ────────────────────────────────────────────────────────


@pytest.mark.django_db
def test_filtro_status_publicacao_seleciona_apenas_publicadas():
    """Mantém no queryset só a designação publicada."""
    publicada = _publicar(criar_ato_designacao(ue=UE))
    criar_ato_designacao(ue=UE)

    filtro = HistoricoDesignacaoFilter(
        data={"status_publicacao": "PUBLICADO"}, queryset=_designacoes()
    )

    assert filtro.is_valid()
    assert list(filtro.qs) == [publicada]


@pytest.mark.django_db
def test_filtro_status_publicacao_nao_publicado():
    """Mantém no queryset só a designação não publicada."""
    publicada = _publicar(criar_ato_designacao(ue=UE))
    nao_publicada = criar_ato_designacao(ue=UE)

    filtro = HistoricoDesignacaoFilter(
        data={"status_publicacao": "NAO_PUBLICADO"}, queryset=_designacoes()
    )

    assert filtro.is_valid()
    assert list(filtro.qs) == [nao_publicada]
    assert publicada not in filtro.qs


@pytest.mark.django_db
def test_filtro_status_publicacao_invalido():
    """Valor fora das choices invalida o filtro."""
    criar_ato_designacao(ue=UE)

    filtro = HistoricoDesignacaoFilter(
        data={"status_publicacao": "INEXISTENTE"}, queryset=_designacoes()
    )

    assert not filtro.is_valid()
    assert "status_publicacao" in filtro.errors


# ── periodo (periodo_after / periodo_before) ─────────────────────────────────


@pytest.mark.django_db
def test_filtro_periodo_after():
    """`periodo_after` mantém designações iniciadas a partir da data."""
    antiga = criar_ato_designacao(ue=UE, data_inicio=datetime.date(2024, 1, 1))
    recente = criar_ato_designacao(
        ue=UE, data_inicio=datetime.date(2026, 10, 10)
    )

    filtro = HistoricoDesignacaoFilter(
        data={"periodo_after": "2026-10-06"}, queryset=_designacoes()
    )

    assert filtro.is_valid()
    assert list(filtro.qs) == [recente]
    assert antiga not in filtro.qs


@pytest.mark.django_db
def test_filtro_periodo_before():
    """`periodo_before` mantém designações iniciadas até a data."""
    antiga = criar_ato_designacao(ue=UE, data_inicio=datetime.date(2024, 1, 1))
    recente = criar_ato_designacao(
        ue=UE, data_inicio=datetime.date(2026, 10, 10)
    )

    filtro = HistoricoDesignacaoFilter(
        data={"periodo_before": "2026-11-10"}, queryset=_designacoes()
    )

    assert filtro.is_valid()
    assert list(filtro.qs) == [antiga, recente]
    assert recente in filtro.qs


@pytest.mark.django_db
def test_filtro_periodo_intervalo():
    """Os dois limites juntos funcionam como intervalo fechado."""
    fora_antes = criar_ato_designacao(
        ue=UE, data_inicio=datetime.date(2026, 10, 5)
    )
    dentro = criar_ato_designacao(
        ue=UE, data_inicio=datetime.date(2026, 10, 20)
    )
    fora_depois = criar_ato_designacao(
        ue=UE, data_inicio=datetime.date(2026, 11, 11)
    )

    filtro = HistoricoDesignacaoFilter(
        data={"periodo_after": "2026-10-06", "periodo_before": "2026-11-10"},
        queryset=_designacoes(),
    )

    assert filtro.is_valid()
    assert list(filtro.qs) == [dentro]
    assert fora_antes not in filtro.qs
    assert fora_depois not in filtro.qs


@pytest.mark.django_db
def test_filtro_periodo_data_invalida():
    """Data em formato inválido invalida o filtro."""
    criar_ato_designacao(ue=UE)

    filtro = HistoricoDesignacaoFilter(
        data={"periodo_after": "data-invalida"}, queryset=_designacoes()
    )

    assert not filtro.is_valid()
    assert "periodo" in filtro.errors


# ── observacao ───────────────────────────────────────────────────────────────


@pytest.mark.django_db
def test_filtro_observacao_em_apostila():
    """Seleciona a designação cuja apostila traz a observação buscada."""
    com_observacao = criar_ato_designacao(ue=UE)
    criar_ato_apostila(
        criar_ato_cessacao(com_observacao), observacao="ssss retificação"
    )
    sem_observacao = criar_ato_designacao(ue=UE)
    criar_ato_apostila(
        criar_ato_cessacao(sem_observacao), observacao="outro texto"
    )

    filtro = HistoricoDesignacaoFilter(
        data={"observacao": "ssss"}, queryset=_designacoes()
    )

    assert filtro.is_valid()
    assert list(filtro.qs) == [com_observacao]


@pytest.mark.django_db
def test_filtro_observacao_em_insubsistencia():
    """Seleciona a designação cuja insubsistência traz a observação."""
    com_observacao = criar_ato_designacao(ue=UE)
    criar_ato_insubsistencia(
        criar_ato_cessacao(com_observacao), observacoes="ssss indevido"
    )
    sem_observacao = criar_ato_designacao(ue=UE)
    criar_ato_insubsistencia(
        criar_ato_cessacao(sem_observacao), observacoes="nada"
    )

    filtro = HistoricoDesignacaoFilter(
        data={"observacao": "ssss"}, queryset=_designacoes()
    )

    assert filtro.is_valid()
    assert list(filtro.qs) == [com_observacao]


@pytest.mark.django_db
def test_filtro_observacao_case_insensitive():
    """A busca por observação ignora maiúsculas e minúsculas."""
    designacao = criar_ato_designacao(ue=UE)
    criar_ato_apostila(
        criar_ato_cessacao(designacao), observacao="SSSS em caixa alta"
    )

    filtro = HistoricoDesignacaoFilter(
        data={"observacao": "ssss"}, queryset=_designacoes()
    )

    assert filtro.is_valid()
    assert list(filtro.qs) == [designacao]


@pytest.mark.django_db
def test_filtro_observacao_sem_correspondencia():
    """Observação inexistente devolve queryset vazio."""
    designacao = criar_ato_designacao(ue=UE)
    criar_ato_apostila(criar_ato_cessacao(designacao), observacao="texto")

    filtro = HistoricoDesignacaoFilter(
        data={"observacao": "ssss"}, queryset=_designacoes()
    )

    assert filtro.is_valid()
    assert list(filtro.qs) == []


@pytest.mark.django_db
def test_filtro_observacao_nao_afeta_designacao_sem_filhos():
    """Designação sem atos relacionados não casa com nenhuma observação."""
    criar_ato_designacao(ue=UE)

    filtro = HistoricoDesignacaoFilter(
        data={"observacao": "ssss"}, queryset=_designacoes()
    )

    assert filtro.is_valid()
    assert list(filtro.qs) == []


# ── combinação de filtros ────────────────────────────────────────────────────


@pytest.mark.django_db
def test_filtros_combinados_ultimo_cenario():
    """Os três filtros juntos restringem pelo E lógico."""
    alvo = criar_ato_designacao(ue=UE, data_inicio=datetime.date(2026, 10, 20))
    _publicar(alvo)
    criar_ato_apostila(
        criar_ato_cessacao(alvo), observacao="ssss com observação"
    )

    # Fora do período
    fora_periodo = criar_ato_designacao(
        ue=UE, data_inicio=datetime.date(2025, 1, 1)
    )
    _publicar(fora_periodo)
    criar_ato_apostila(
        criar_ato_cessacao(fora_periodo), observacao="ssss com observação"
    )

    # Sem a observação
    sem_observacao = criar_ato_designacao(
        ue=UE, data_inicio=datetime.date(2026, 10, 21)
    )
    _publicar(sem_observacao)

    filtro = HistoricoDesignacaoFilter(
        data={
            "status_publicacao": "PUBLICADO",
            "periodo_after": "2026-10-06",
            "periodo_before": "2026-11-10",
            "observacao": "ssss",
        },
        queryset=_designacoes(),
    )

    assert filtro.is_valid()
    assert list(filtro.qs) == [alvo]


# ── endpoint: os filtros são aplicados na resposta ───────────────────────────


@pytest.mark.django_db
def test_endpoint_filtra_por_status_publicacao(auth_client):
    """`status_publicacao` na query string filtra as designações."""
    publicada = _publicar(criar_ato_designacao(ue=UE))
    criar_ato_designacao(ue=UE)

    response = auth_client.get(_url(), {"status_publicacao": "PUBLICADO"})

    assert response.status_code == 200
    assert [item["id"] for item in response.data] == [publicada.pk]


@pytest.mark.django_db
def test_endpoint_filtra_por_periodo(auth_client):
    """`periodo_after`/`periodo_before` filtram pela data de início."""
    dentro = criar_ato_designacao(
        ue=UE, data_inicio=datetime.date(2026, 10, 20)
    )
    criar_ato_designacao(ue=UE, data_inicio=datetime.date(2025, 1, 1))

    response = auth_client.get(
        _url(),
        {"periodo_after": "2026-10-06", "periodo_before": "2026-11-10"},
    )

    assert response.status_code == 200
    assert [item["id"] for item in response.data] == [dentro.pk]


@pytest.mark.django_db
def test_endpoint_filtra_por_observacao(auth_client):
    """`observacao` filtra as designações com ato relacionado."""
    alvo = criar_ato_designacao(ue=UE)
    criar_ato_apostila(criar_ato_cessacao(alvo), observacao="ssss")
    criar_ato_designacao(ue=UE)

    response = auth_client.get(_url(), {"observacao": "ssss"})

    assert response.status_code == 200
    assert [item["id"] for item in response.data] == [alvo.pk]


@pytest.mark.django_db
def test_endpoint_filtros_combinados(auth_client):
    """Cenário completo de query string: todos os filtros aplicados."""
    alvo = criar_ato_designacao(ue=UE, data_inicio=datetime.date(2026, 10, 20))
    criar_ato_apostila(criar_ato_cessacao(alvo), observacao="ssss")
    # Publicada e no período, mas sem a observação.
    criar_ato_designacao(ue=UE, data_inicio=datetime.date(2026, 10, 21))

    response = auth_client.get(
        _url(),
        {
            "status_publicacao": "NAO_PUBLICADO",
            "periodo_after": "2026-10-06",
            "periodo_before": "2026-11-10",
            "observacao": "ssss",
        },
    )

    assert response.status_code == 200
    assert [item["id"] for item in response.data] == [alvo.pk]


@pytest.mark.django_db
def test_endpoint_filtro_sem_resultado_devolve_lista_vazia(auth_client):
    """Nenhuma designação satisfazendo os filtros devolve `[]`."""
    criar_ato_designacao(ue=UE, data_inicio=datetime.date(2024, 1, 1))

    response = auth_client.get(_url(), {"periodo_after": "2026-10-06"})

    assert response.status_code == 200
    assert response.data == []


@pytest.mark.django_db
def test_endpoint_status_publicacao_invalido_retorna_400(auth_client):
    """Status fora das choices devolve 400 com o campo do erro."""
    criar_ato_designacao(ue=UE)

    response = auth_client.get(_url(), {"status_publicacao": "XPTO"})

    assert response.status_code == 400
    assert "status_publicacao" in response.data


@pytest.mark.django_db
def test_endpoint_data_invalida_retorna_400(auth_client):
    """Data em formato inválido devolve 400 com o campo do erro."""
    criar_ato_designacao(ue=UE)

    response = auth_client.get(_url(), {"periodo_after": "data-invalida"})

    assert response.status_code == 400
    assert "periodo" in response.data


@pytest.mark.django_db
def test_endpoint_ignora_parametros_desconhecidos(auth_client):
    """Query params que não são filtros não quebram a resposta."""
    designacao = criar_ato_designacao(ue=UE)

    response = auth_client.get(_url(), {"foo": "bar", "page": 2})

    assert response.status_code == 200
    assert [item["id"] for item in response.data] == [designacao.pk]


@pytest.mark.django_db
def test_endpoint_mantem_atos_relacionados_completos_ao_filtrar(auth_client):
    """O filtro escolhe a designação, mas não corta o histórico dela."""
    designacao = criar_ato_designacao(ue=UE)
    cessacao = criar_ato_cessacao(designacao)
    apostila = criar_ato_apostila(cessacao, observacao="ssss")
    insubsistencia = criar_ato_insubsistencia(cessacao, observacoes="outra")

    response = auth_client.get(_url(), {"observacao": "ssss"})

    assert response.status_code == 200
    assert len(response.data) == 1
    atos = response.data[0]["atos_relacionados"]
    assert [ato["id"] for ato in atos] == [
        cessacao.pk,
        apostila.pk,
        insubsistencia.pk,
    ]
    # A observação dos atos que não casaram com o filtro continua na resposta.
    assert atos[2]["observacao"] == "outra"


@pytest.mark.django_db
def test_filtro_nao_cresce_o_numero_de_consultas(django_assert_num_queries):
    """Filtrar mantém o endpoint em uma única consulta."""
    designacao = criar_ato_designacao(ue=UE)
    criar_ato_apostila(criar_ato_cessacao(designacao), observacao="ssss")

    with django_assert_num_queries(1):
        resultado = HistoricoDesignacaoService.listar_por_ue(
            UE,
            {
                "status_publicacao": "NAO_PUBLICADO",
                "periodo_after": "2024-01-01",
                "observacao": "ssss",
            },
        )

    assert [designacao.pk] == [ato.pk for ato in resultado]
