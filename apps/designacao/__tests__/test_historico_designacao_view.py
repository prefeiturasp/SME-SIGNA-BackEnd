"""Testes da view de histórico de designações por unidade escolar."""

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
from apps.designacao.api.serializers.historico_designacao_serializer import (
    HistoricoDesignacaoSerializer,
)
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


# ── Filtro por UE e dados principais ─────────────────────────────────────────


@pytest.mark.django_db
def test_lista_designacoes_da_ue_com_dados_principais(auth_client):
    """Retorna portaria, cargo, servidor, data e vigência da designação."""
    criar_ato_designacao(
        ue=UE,
        dre="DRE-1",
        dre_nome="DRE Teste",
        unidade_proponente="Escola Teste",
        indicado_nome_servidor="Maria Silva",
        indicado_cargo_base="Professor",
        data_inicio=datetime.date(2024, 2, 5),
        numero_portaria=123,
    )
    criar_ato_designacao(ue="099999")

    response = auth_client.get(_url())

    assert response.status_code == 200
    assert len(response.data) == 1
    item = response.data[0]
    assert item["ue"] == UE
    assert item["portaria"] == "123/2024"
    assert item["cargo"] == "Professor"
    assert item["servidor_indicado"] == "Maria Silva"
    assert item["data_inicio"] == "2024-02-05"
    assert item["vigente"] is True
    assert item["cessada_em"] is None
    assert item["atos_relacionados"] == []


@pytest.mark.django_db
def test_ue_sem_designacoes_retorna_lista_vazia(auth_client):
    """Unidade sem designações devolve 200 com lista vazia."""
    response = auth_client.get(_url("999999"))

    assert response.status_code == 200
    assert response.data == []


@pytest.mark.django_db
@pytest.mark.parametrize("codigo", ["19453", "019453", "00019453"])
def test_codigo_ue_aceita_variacoes_de_zeros_a_esquerda(auth_client, codigo):
    """A consulta funciona com e sem zeros à esquerda no código da UE."""
    criar_ato_designacao(ue="019453")

    response = auth_client.get(_url(codigo))

    assert response.status_code == 200
    assert len(response.data) == 1


@pytest.mark.django_db
def test_designacoes_ordenadas_da_mais_recente_para_a_mais_antiga(
    auth_client,
):
    """Ordena as designações pela data de início decrescente."""
    antiga = criar_ato_designacao(ue=UE, data_inicio=datetime.date(2020, 1, 1))
    recente = criar_ato_designacao(
        ue=UE, data_inicio=datetime.date(2024, 1, 1)
    )

    response = auth_client.get(_url())

    assert [item["id"] for item in response.data] == [recente.pk, antiga.pk]


# ── Vigência e cessação ──────────────────────────────────────────────────────


@pytest.mark.django_db
def test_cessacao_ativa_informa_cessada_em_e_nao_fica_vigente(auth_client):
    """Cessação válida preenche `cessada_em` e encerra a vigência."""
    designacao = criar_ato_designacao(ue=UE)
    criar_ato_cessacao(
        designacao,
        numero_portaria=456,
        doc=datetime.date(2024, 3, 2),
        data_cessacao=datetime.date(2024, 3, 1),
    )

    response = auth_client.get(_url())

    item = response.data[0]
    assert item["vigente"] is False
    assert item["cessada_em"] == "2024-03-01"

    ato = item["atos_relacionados"][0]
    assert ato["tipo"] == "CESSACAO"
    assert ato["tipo_de_ato"] == "Cessação"
    assert ato["data_do_ato"] == "2024-03-02"
    assert ato["portaria"] == "456/2024"
    assert ato["observacao"] is None


@pytest.mark.django_db
def test_cessacao_insubsistente_nao_marca_cessada_em(auth_client):
    """Cessação tornada sem efeito não encerra a designação."""
    designacao = criar_ato_designacao(ue=UE)
    cessacao = criar_ato_cessacao(designacao)
    cessacao.ativo = False
    cessacao.save(update_fields=["ativo"])

    response = auth_client.get(_url())

    item = response.data[0]
    assert item["vigente"] is True
    assert item["cessada_em"] is None


@pytest.mark.django_db
def test_designacao_com_data_fim_no_passado_nao_esta_vigente(auth_client):
    """Designação com período encerrado não está vigente."""
    criar_ato_designacao(ue=UE, data_fim=datetime.date(2020, 1, 1))

    response = auth_client.get(_url())

    assert response.data[0]["vigente"] is False


# ── Lista plana de atos relacionados ────────────────────────────────────────


@pytest.mark.django_db
def test_atos_relacionados_em_lista_plana_com_todos_os_niveis(auth_client):
    """Todos os atos derivados vêm em um único array, sem aninhamento."""
    designacao = criar_ato_designacao(
        ue=UE, indicado_nome_servidor="Maria Silva"
    )
    cessacao = criar_ato_cessacao(
        designacao, numero_portaria=456, doc=datetime.date(2024, 3, 1)
    )
    apostila = criar_ato_apostila(
        cessacao,
        observacao="Apostila da cessação",
        numero_portaria=457,
        doc=datetime.date(2024, 4, 1),
    )
    insubsistencia = criar_ato_insubsistencia(
        apostila,
        numero_portaria=458,
        doc=datetime.date(2024, 5, 1),
        observacoes="Anulação da apostila",
    )

    response = auth_client.get(_url())

    atos = response.data[0]["atos_relacionados"]
    assert [ato["id"] for ato in atos] == [
        cessacao.pk,
        apostila.pk,
        insubsistencia.pk,
    ]
    assert [ato["tipo"] for ato in atos] == [
        "CESSACAO",
        "APOSTILA",
        "INSUBSISTENCIA",
    ]
    assert [ato["nivel"] for ato in atos] == [1, 2, 3]
    assert [ato["ato_pai_id"] for ato in atos] == [
        designacao.pk,
        cessacao.pk,
        apostila.pk,
    ]
    # A lista é plana: nenhum item carrega atos aninhados.
    for ato in atos:
        assert "atos_relacionados" not in ato


@pytest.mark.django_db
def test_atos_relacionados_trazem_dados_de_cada_ato(auth_client):
    """Cada item da lista traz data, portaria, nome, observação e tipo."""
    designacao = criar_ato_designacao(
        ue=UE, indicado_nome_servidor="Maria Silva"
    )
    cessacao = criar_ato_cessacao(
        designacao, numero_portaria=456, doc=datetime.date(2024, 3, 1)
    )
    apostila = criar_ato_apostila(
        cessacao,
        observacao="Apostila da cessação",
        numero_portaria=457,
        doc=datetime.date(2024, 4, 1),
    )
    criar_ato_insubsistencia(
        apostila,
        numero_portaria=458,
        doc=datetime.date(2024, 5, 1),
        observacoes="Anulação da apostila",
    )

    response = auth_client.get(_url())

    cessacao_json, apostila_json, insubsistencia_json = response.data[0][
        "atos_relacionados"
    ]

    assert cessacao_json["tipo_de_ato"] == "Cessação"
    assert cessacao_json["data_do_ato"] == "2024-03-01"
    assert cessacao_json["portaria"] == "456/2024"
    assert cessacao_json["nome_display"] == "Maria Silva"
    assert cessacao_json["observacao"] is None

    assert apostila_json["tipo_de_ato"] == "Apostila de Cessação"
    assert apostila_json["data_do_ato"] == "2024-04-01"
    assert apostila_json["portaria"] == "457/2024"
    assert apostila_json["nome_display"] == "Maria Silva"
    assert apostila_json["observacao"] == "Apostila da cessação"

    assert insubsistencia_json["tipo_de_ato"] == "Anulação de Apostila"
    assert insubsistencia_json["data_do_ato"] == "2024-05-01"
    assert insubsistencia_json["portaria"] == "458/2024"
    assert insubsistencia_json["nome_display"] == "Maria Silva"
    assert insubsistencia_json["observacao"] == "Anulação da apostila"


@pytest.mark.django_db
def test_tipo_de_ato_de_filho_direto_da_designacao(auth_client):
    """Atos filhos diretos da designação citam o tipo do pai."""
    designacao = criar_ato_designacao(ue=UE)
    criar_ato_apostila(designacao, observacao="Apostila direta")
    criar_ato_insubsistencia(designacao, observacoes="Insubsistência direta")

    response = auth_client.get(_url())

    rotulos = {
        ato["tipo"]: ato["tipo_de_ato"]
        for ato in response.data[0]["atos_relacionados"]
    }
    assert rotulos["APOSTILA"] == "Apostila de Designação"
    assert rotulos["INSUBSISTENCIA"] == "Insubsistência de Designação"


@pytest.mark.django_db
def test_ato_sem_numero_de_portaria_retorna_portaria_nula(auth_client):
    """Ato sem número de portaria não quebra a formatação."""
    designacao = criar_ato_designacao(ue=UE)
    criar_ato_apostila(designacao, numero_portaria=None)

    response = auth_client.get(_url())

    ato = response.data[0]["atos_relacionados"][0]
    assert ato["numero_portaria"] is None
    assert ato["portaria"] is None


# ── Flag do último ato ativo e vigente ──────────────────────────────────────


@pytest.mark.django_db
def test_ultimo_ato_vigente_marca_a_cessacao_ativa(auth_client):
    """Com uma única cessação ativa, ela é o último ato vigente."""
    designacao = criar_ato_designacao(ue=UE)
    cessacao = criar_ato_cessacao(designacao)

    response = auth_client.get(_url())

    atos = response.data[0]["atos_relacionados"]
    assert atos[0]["id"] == cessacao.pk
    assert atos[0]["ultimo_ato_vigente"] is True


@pytest.mark.django_db
def test_apenas_um_ato_recebe_a_flag_de_ultimo_vigente(auth_client):
    """Só o ato mais recente que continua ativo fica marcado."""
    designacao = criar_ato_designacao(ue=UE)
    cessacao = criar_ato_cessacao(designacao)
    apostila = criar_ato_apostila(cessacao, numero_portaria=457)
    insubsistencia = criar_ato_insubsistencia(apostila, numero_portaria=458)

    # A insubsistência desfaz a apostila (InsubsistenciaService.criar).
    apostila.ativo = False
    apostila.save(update_fields=["ativo"])

    response = auth_client.get(_url())

    atos = response.data[0]["atos_relacionados"]
    marcados = {ato["id"]: ato["ultimo_ato_vigente"] for ato in atos}
    assert marcados == {
        cessacao.pk: False,
        apostila.pk: False,
        insubsistencia.pk: True,
    }
    assert sum(ato["ultimo_ato_vigente"] for ato in atos) == 1


@pytest.mark.django_db
def test_flag_ignora_ato_desfeito_e_marca_o_anterior_ativo(auth_client):
    """O ato desfeito não recebe a flag; vale o anterior ainda ativo."""
    designacao = criar_ato_designacao(ue=UE)
    cessacao = criar_ato_cessacao(designacao)
    apostila = criar_ato_apostila(cessacao, numero_portaria=457)

    # Apostila anulada: deixa de valer mesmo sendo o ato mais recente.
    apostila.ativo = False
    apostila.save(update_fields=["ativo"])

    response = auth_client.get(_url())

    atos = response.data[0]["atos_relacionados"]
    marcados = {ato["id"]: ato["ultimo_ato_vigente"] for ato in atos}
    assert marcados == {cessacao.pk: True, apostila.pk: False}


@pytest.mark.django_db
def test_sem_atos_ativos_nenhum_item_recebe_a_flag(auth_client):
    """Quando todos os atos foram desfeitos, nada é marcado."""
    designacao = criar_ato_designacao(ue=UE)
    cessacao = criar_ato_cessacao(designacao)
    cessacao.ativo = False
    cessacao.save(update_fields=["ativo"])

    response = auth_client.get(_url())

    atos = response.data[0]["atos_relacionados"]
    assert [ato["ultimo_ato_vigente"] for ato in atos] == [False]


# ── Performance e autenticação ───────────────────────────────────────────────


@pytest.mark.django_db
def test_listagem_e_serializacao_nao_geram_consultas_extras(
    django_assert_num_queries,
):
    """Carrega tudo em uma consulta e serializa sem ir ao banco."""
    designacao = criar_ato_designacao(ue=UE)
    cessacao = criar_ato_cessacao(designacao)
    apostila = criar_ato_apostila(cessacao)
    criar_ato_insubsistencia(apostila)

    with django_assert_num_queries(1):
        designacoes = HistoricoDesignacaoService.listar_por_ue(UE)

    with django_assert_num_queries(0):
        payload = HistoricoDesignacaoSerializer(designacoes, many=True).data

    niveis = [ato["nivel"] for ato in payload[0]["atos_relacionados"]]
    assert niveis == [1, 2, 3]


@pytest.mark.django_db
def test_numero_de_consultas_nao_cresce_com_o_volume(
    django_assert_num_queries,
):
    """O custo é constante: mais designações e atos, mesmas consultas."""
    for indice in range(5):
        designacao = criar_ato_designacao(
            ue=UE, data_inicio=datetime.date(2020 + indice, 1, 1)
        )
        cessacao = criar_ato_cessacao(designacao)
        apostila = criar_ato_apostila(cessacao)
        criar_ato_insubsistencia(apostila)

    with django_assert_num_queries(1):
        designacoes = HistoricoDesignacaoService.listar_por_ue(UE)

    with django_assert_num_queries(0):
        payload = HistoricoDesignacaoSerializer(designacoes, many=True).data

    assert len(payload) == 5
    assert all(len(item["atos_relacionados"]) == 3 for item in payload)


@pytest.mark.django_db
def test_texto_sei_nao_e_carregado():
    """O texto da portaria é adiado: não trafega no histórico."""
    criar_ato_designacao(ue=UE)
    cessacao = criar_ato_cessacao(
        criar_ato_designacao(ue=UE), numero_portaria=456
    )
    cessacao.texto_sei = "texto longo da portaria"
    cessacao.save(update_fields=["texto_sei"])

    designacoes = HistoricoDesignacaoService.listar_por_ue(UE)

    for designacao in designacoes:
        assert "texto_sei" in designacao.get_deferred_fields()


@pytest.mark.django_db
def test_requer_autenticacao():
    """Endpoint exige usuário autenticado."""
    response = APIClient().get(_url())

    assert response.status_code in (401, 403)
