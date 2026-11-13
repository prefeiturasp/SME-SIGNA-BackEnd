"""Testes dos filtros do histórico de designações por unidade escolar.

Cobre os filtros `tipo`, `status_publicacao`, `periodo` (params
`periodo_after` e `periodo_before`) e `observacao`, tanto no ``FilterSet``
(unidade) quanto no endpoint (integração).
"""

import datetime
import secrets

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
    client.credentials(
        HTTP_AUTHORIZATION=f"Bearer {AccessToken.for_user(user)}"
    )
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


# ── tipo ─────────────────────────────────────────────────────────────────────


@pytest.mark.django_db
def test_filtro_tipo_designacao_mantem_as_designacoes():
    """`DESIGNACAO` casa com a própria designação do histórico."""
    designacao = criar_ato_designacao(ue=UE)
    criar_ato_cessacao(designacao)

    filtro = HistoricoDesignacaoFilter(
        data={"tipo": "DESIGNACAO"}, queryset=_designacoes()
    )

    assert filtro.is_valid()
    assert list(filtro.qs) == [designacao]


@pytest.mark.django_db
def test_filtro_tipo_designacao_cessacao_mantem_todo_o_historico():
    """`DESIGNACAO_CESSACAO` é a união de designação e cessação.

    Como toda designação é do tipo `DESIGNACAO`, a união equivale ao
    histórico inteiro: o valor não restringe quais designações entram.
    """
    com_cessacao = criar_ato_designacao(ue=UE)
    criar_ato_cessacao(com_cessacao)
    sem_cessacao = criar_ato_designacao(ue=UE)

    filtro = HistoricoDesignacaoFilter(
        data={"tipo": "DESIGNACAO_CESSACAO"}, queryset=_designacoes()
    )

    assert filtro.is_valid()
    assert set(filtro.qs) == {com_cessacao, sem_cessacao}


@pytest.mark.django_db
def test_filtro_tipo_cessacao_exige_ato_derivado():
    """`CESSACAO` mantém só a designação que tem cessação."""
    com_cessacao = criar_ato_designacao(ue=UE)
    criar_ato_cessacao(com_cessacao)
    criar_ato_designacao(ue=UE)

    filtro = HistoricoDesignacaoFilter(
        data={"tipo": "CESSACAO"}, queryset=_designacoes()
    )

    assert filtro.is_valid()
    assert list(filtro.qs) == [com_cessacao]


@pytest.mark.django_db
def test_filtro_tipo_apostila_inclui_apostila_de_qualquer_pai():
    """`APOSTILA` não olha o tipo do pai do ato derivado."""
    de_designacao = criar_ato_designacao(ue=UE)
    criar_ato_apostila(de_designacao)
    de_cessacao = criar_ato_designacao(ue=UE)
    criar_ato_apostila(criar_ato_cessacao(de_cessacao))
    sem_apostila = criar_ato_designacao(ue=UE)

    filtro = HistoricoDesignacaoFilter(
        data={"tipo": "APOSTILA"}, queryset=_designacoes()
    )

    assert filtro.is_valid()
    assert set(filtro.qs) == {de_designacao, de_cessacao}
    assert sem_apostila not in filtro.qs


@pytest.mark.django_db
def test_filtro_tipo_insubsistencia_inclui_insubsistencia_de_qualquer_pai():
    """`INSUBSISTENCIA` não olha o tipo do pai do ato derivado."""
    da_designacao = criar_ato_designacao(ue=UE)
    criar_ato_insubsistencia(da_designacao)
    da_cessacao = criar_ato_designacao(ue=UE)
    criar_ato_insubsistencia(criar_ato_cessacao(da_cessacao))
    da_apostila = criar_ato_designacao(ue=UE)
    criar_ato_insubsistencia(criar_ato_apostila(da_apostila))
    sem_insubsistencia = criar_ato_designacao(ue=UE)

    filtro = HistoricoDesignacaoFilter(
        data={"tipo": "INSUBSISTENCIA"}, queryset=_designacoes()
    )

    assert filtro.is_valid()
    assert set(filtro.qs) == {da_designacao, da_cessacao, da_apostila}
    assert sem_insubsistencia not in filtro.qs


@pytest.mark.django_db
def test_filtro_tipo_composto_usa_o_tipo_do_pai():
    """`APOSTILA_CESSACAO` não casa com apostila filha da designação."""
    da_cessacao = criar_ato_designacao(ue=UE)
    criar_ato_apostila(criar_ato_cessacao(da_cessacao))
    da_designacao = criar_ato_designacao(ue=UE)
    criar_ato_apostila(da_designacao)

    filtro = HistoricoDesignacaoFilter(
        data={"tipo": "APOSTILA_CESSACAO"}, queryset=_designacoes()
    )

    assert filtro.is_valid()
    assert list(filtro.qs) == [da_cessacao]


@pytest.mark.django_db
def test_filtro_tipo_composto_de_insubsistencia_de_apostila():
    """`INSUBSISTENCIA_APOSTILA` casa só com insubsistência de apostila."""
    da_apostila = criar_ato_designacao(ue=UE)
    criar_ato_insubsistencia(criar_ato_apostila(da_apostila))
    da_cessacao = criar_ato_designacao(ue=UE)
    criar_ato_insubsistencia(criar_ato_cessacao(da_cessacao))

    filtro = HistoricoDesignacaoFilter(
        data={"tipo": "INSUBSISTENCIA_APOSTILA"}, queryset=_designacoes()
    )

    assert filtro.is_valid()
    assert list(filtro.qs) == [da_apostila]


@pytest.mark.django_db
def test_filtro_tipo_tornar_sem_efeito():
    """`INSUBSISTENCIA_INSUBSISTENCIA` casa só com o ato que desfaz outro."""
    sem_efeito = criar_ato_designacao(ue=UE)
    criar_ato_insubsistencia(criar_ato_insubsistencia(sem_efeito))
    da_designacao = criar_ato_designacao(ue=UE)
    criar_ato_insubsistencia(da_designacao)

    filtro = HistoricoDesignacaoFilter(
        data={"tipo": "INSUBSISTENCIA_INSUBSISTENCIA"},
        queryset=_designacoes(),
    )

    assert filtro.is_valid()
    assert list(filtro.qs) == [sem_efeito]


@pytest.mark.django_db
def test_filtro_tipo_combina_em_e_com_os_demais_filtros():
    """`tipo` restringe junto com os outros parâmetros."""
    publicada = criar_ato_designacao(ue=UE)
    _publicar(publicada)
    criar_ato_cessacao(publicada)
    nao_publicada = criar_ato_designacao(ue=UE)
    criar_ato_cessacao(nao_publicada)

    filtro = HistoricoDesignacaoFilter(
        data={"tipo": "CESSACAO", "status_publicacao": "PUBLICADO"},
        queryset=_designacoes(),
    )

    assert filtro.is_valid()
    assert list(filtro.qs) == [publicada]


@pytest.mark.django_db
def test_filtro_tipo_invalido():
    """Valor fora das opções da listagem de atos invalida o filtro."""
    criar_ato_designacao(ue=UE)

    filtro = HistoricoDesignacaoFilter(
        data={"tipo": "INEXISTENTE"}, queryset=_designacoes()
    )

    assert not filtro.is_valid()
    assert "tipo" in filtro.errors


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
def test_endpoint_filtra_por_cargo_da_vaga_e_preserva_atos(auth_client):
    alvo = criar_ato_designacao(
        ue=UE, cargo_vaga=3360, indicado_codigo_cargo_base=3085
    )
    apostila = criar_ato_apostila(alvo)
    criar_ato_designacao(
        ue=UE, cargo_vaga=3085, indicado_codigo_cargo_base=3360
    )
    criar_ato_designacao(ue="999999", cargo_vaga=3360)

    response = auth_client.get(_url(), {"cargo": "3360"})

    assert response.status_code == 200
    assert [item["id"] for item in response.data] == [alvo.pk]
    assert [ato["id"] for ato in response.data[0]["atos_relacionados"]] == [
        apostila.pk
    ]


@pytest.mark.django_db
def test_endpoint_combina_cargo_e_status(auth_client):
    alvo = _publicar(criar_ato_designacao(ue=UE, cargo_vaga=3360))
    criar_ato_designacao(ue=UE, cargo_vaga=3360)
    _publicar(criar_ato_designacao(ue=UE, cargo_vaga=3085))

    response = auth_client.get(
        _url(), {"cargo": "3360", "status_publicacao": "PUBLICADO"}
    )

    assert response.status_code == 200
    assert [item["id"] for item in response.data] == [alvo.pk]


@pytest.mark.django_db
def test_endpoint_rejeita_cargo_invalido(auth_client):
    response = auth_client.get(_url(), {"cargo": "invalido"})
    assert response.status_code == 400
    assert "cargo" in response.data


@pytest.mark.django_db
def test_endpoint_cargo_sem_resultados(auth_client):
    criar_ato_designacao(ue=UE, cargo_vaga=3085)
    response = auth_client.get(_url(), {"cargo": "3360"})
    assert response.status_code == 200
    assert response.data == []


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
def test_endpoint_filtra_por_tipo_e_mantem_o_historico(auth_client):
    """`tipo` escolhe a designação e devolve os atos relacionados inteiros."""
    alvo = criar_ato_designacao(ue=UE)
    cessacao = criar_ato_cessacao(alvo)
    apostila = criar_ato_apostila(cessacao)
    criar_ato_designacao(ue=UE)

    response = auth_client.get(_url(), {"tipo": "CESSACAO"})

    assert response.status_code == 200
    assert [item["id"] for item in response.data] == [alvo.pk]
    assert [ato["id"] for ato in response.data[0]["atos_relacionados"]] == [
        apostila.pk,
        cessacao.pk,
    ]


@pytest.mark.django_db
def test_endpoint_tipo_invalido_retorna_400(auth_client):
    """Tipo de ato fora das opções devolve 400."""
    criar_ato_designacao(ue=UE)

    response = auth_client.get(_url(), {"tipo": "INEXISTENTE"})

    assert response.status_code == 400
    assert "tipo" in response.data


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
        insubsistencia.pk,
        apostila.pk,
        cessacao.pk,
    ]
    # A observação dos atos que não casaram com o filtro continua na resposta.
    assert atos[0]["observacoes"] == "outra"


@pytest.mark.django_db
def test_filtro_nao_cresce_o_numero_de_consultas(django_assert_num_queries):
    """Filtrar mantém o endpoint em uma única consulta."""
    designacao = criar_ato_designacao(ue=UE)
    criar_ato_apostila(criar_ato_cessacao(designacao), observacao="ssss")

    with django_assert_num_queries(1):
        resultado = HistoricoDesignacaoService.listar_por_ue(
            UE,
            {
                "tipo": "APOSTILA",
                "status_publicacao": "NAO_PUBLICADO",
                "periodo_after": "2024-01-01",
                "observacao": "ssss",
            },
        )

    assert [designacao.pk] == [ato.pk for ato in resultado]
