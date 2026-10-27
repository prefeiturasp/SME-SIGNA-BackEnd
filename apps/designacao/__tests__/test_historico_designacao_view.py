"""Testes da view de histórico de designações por unidade escolar."""

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
from apps.designacao.api.serializers.historico_designacao_serializer import (
    HistoricoDesignacaoSerializer,
)
from apps.designacao.models.ato_administrativo import AtoAdministrativo
from apps.designacao.models.designacao import ImpedimentoSubstituicao
from apps.designacao.services.historico_designacao_service import (
    HistoricoDesignacaoService,
)
from apps.gestao.models.cargo_base import CargoBase

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
    assert item["nome"] == "Maria Silva"
    assert item["data_inicio"] == "2024-02-05"
    assert item["vigente"] is True
    assert item["cessada_em"] is None
    assert item["atos_relacionados"] == []


# ── Paridade com atos administrativos e designação detalhe ───────────────────


CAMPOS_ATO = {
    "id",
    "tipo",
    "tipo_de_ato",
    "status",
    "status_publicacao",
    "numero_portaria",
    "ano_vigente",
    "sei_numero",
    "doc",
    "portaria",
    "ato_pai_id",
    "ato_raiz_id",
    "criado_em",
    "criado_por_nome",
}

CAMPOS_DESIGNACAO_DETALHE = {
    "ue",
    "dre",
    "dre_nome",
    "unidade_proponente",
    "codigo_hierarquico",
    "funcionarios_da_unidade",
    "indicado_nome_civil",
    "indicado_nome_servidor",
    "indicado_rf",
    "indicado_vinculo",
    "indicado_cargo_base",
    "indicado_codigo_cargo_base",
    "indicado_lotacao",
    "indicado_cargo_sobreposto",
    "indicado_codigo_cargo_sobreposto",
    "indicado_local_exercicio",
    "indicado_local_servico",
    "indicado_categoria",
    "indicado_codigo_ue_lotacao",
    "indicado_possui_cargo_sobreposto",
    "titular_nome_civil",
    "titular_nome_servidor",
    "titular_rf",
    "titular_vinculo",
    "titular_cargo_base",
    "titular_codigo_cargo_base",
    "titular_lotacao",
    "titular_cargo_sobreposto",
    "titular_codigo_cargo_sobreposto",
    "titular_local_exercicio",
    "titular_local_servico",
    "data_inicio",
    "data_fim",
    "carater_excepcional",
    "com_afastamento",
    "possui_pendencia",
    "pendencias",
    "motivo_afastamento",
    "informacoes_adicionais",
    "detalhe_para_quadro_de_historico_por_ano",
    "impedimento_substituicao",
    "impedimento_substituicao_detail",
    "impedimento_display",
    "tipo_vaga",
    "tipo_vaga_display",
    "cargo_vaga",
    "cargo_vaga_display",
}

CAMPOS_ATO_RELACIONADO = CAMPOS_ATO | {
    "ativo",
    "data_designacao",
    "data_cessacao",
    "nome",
    "cargo",
    "rf",
    "observacoes",
    "tipo_insubsistencia",
    "tipo_apostila",
    "nivel",
    "ultimo_ato_vigente",
}


@pytest.mark.django_db
def test_payload_da_designacao_tem_os_campos_de_atos_e_do_detalhe(
    auth_client,
):
    """A designação expõe os mesmos campos de atos e de designação detalhe.

    Além deles, vêm os campos próprios do histórico.
    """
    criar_ato_designacao(
        ue=UE,
        indicado_nome_servidor="Maria Silva",
        indicado_rf="1234567",
        indicado_cargo_base="Professor",
        indicado_cargo_sobreposto="Diretor",
        tipo_vaga="VAGO",
        cargo_vaga=3360,
    )

    response = auth_client.get(_url())

    item = response.data[0]
    assert set(item) >= CAMPOS_ATO
    assert set(item) >= CAMPOS_DESIGNACAO_DETALHE
    assert {"vigente", "cessada_em", "atos_relacionados"} <= set(item)

    # Nomenclatura de atos administrativos.
    assert item["tipo"] == "DESIGNACAO"
    assert item["tipo_de_ato"] == "Designação"
    assert item["status"] == "ativo"
    assert item["status_publicacao"] == "NAO_PUBLICADO"
    assert item["nome"] == "Maria Silva"
    assert item["rf"] == "1234567"
    # `cargo` é o sobreposto, com fallback para o base.
    assert item["cargo"] == "Diretor"
    assert item["indicado_cargo_base"] == "Professor"


@pytest.mark.django_db
def test_status_publicacao_acompanha_o_cadastro(auth_client):
    """`status_publicacao` e `doc` refletem a publicação no D.O."""
    criar_ato_designacao(ue=UE, doc=datetime.date(2024, 3, 1))
    AtoAdministrativo.objects.filter(tipo="DESIGNACAO").update(
        status_publicacao=AtoAdministrativo.StatusPublicacao.PUBLICADO
    )

    item = auth_client.get(_url()).data[0]

    assert item["status_publicacao"] == "PUBLICADO"
    assert item["doc"] == "2024-03-01"


@pytest.mark.django_db
def test_criado_por_nome_e_preenchido(auth_client):
    """`criado_por_nome` segue o padrão de atos administrativos."""
    usuario = User.objects.first()
    ato = criar_ato_designacao(ue=UE)
    ato.criado_por = usuario
    ato.save(update_fields=["criado_por"])

    item = auth_client.get(_url()).data[0]

    assert item["criado_por_nome"] == (usuario.name or usuario.username)


@pytest.mark.django_db
def test_impedimento_e_vaga_tem_displays(auth_client):
    """`impedimento_*` e `tipo_vaga_display` vêm como em designacoes/<id>."""
    impedimento = ImpedimentoSubstituicao.objects.create(
        codigo="LIC_MEDICA_TESTE", descricao="Por licença médica"
    )
    criar_ato_designacao(
        ue=UE,
        impedimento_substituicao=impedimento,
        tipo_vaga="DISPONIVEL",
    )

    item = auth_client.get(_url()).data[0]

    assert item["impedimento_substituicao"] == impedimento.pk
    assert item["impedimento_substituicao_detail"] == {
        "id": impedimento.pk,
        "codigo": "LIC_MEDICA_TESTE",
        "descricao": "Por licença médica",
    }
    assert item["impedimento_display"] == "Por licença médica"
    assert item["tipo_vaga_display"] == "Cargo Disponível"
    assert item["cargo_vaga_display"] is None


@pytest.mark.django_db
def test_cargo_vaga_display_usa_o_cadastro_de_cargos(auth_client):
    """`cargo_vaga_display` traz a descrição completa do CargoBase."""
    cargo, _criado = CargoBase.objects.get_or_create(
        codigo_cargo="9999",
        defaults={
            "descricao_resumida": "Cargo de Teste",
            "descricao_completa": "CARGO DE TESTE PARA HISTÓRICO",
            "grupamento": CargoBase.Grupamento.GESTORES_EDUCACAO,
            "situacao_funcional": CargoBase.SituacaoFuncional.EFETIVO,
        },
    )
    criar_ato_designacao(ue=UE, cargo_vaga=int(cargo.codigo_cargo))

    item = auth_client.get(_url()).data[0]

    assert item["cargo_vaga"] == 9999
    assert item["cargo_vaga_display"] == "CARGO DE TESTE PARA HISTÓRICO"


@pytest.mark.django_db
def test_ato_relacionado_tem_campos_de_atos_administrativos(auth_client):
    """Itens de `atos_relacionados` seguem a listagem de atos."""
    designacao = criar_ato_designacao(ue=UE, indicado_rf="1234567")
    cessacao = criar_ato_cessacao(
        designacao, numero_portaria=456, doc=datetime.date(2024, 3, 1)
    )
    apostila = criar_ato_apostila(cessacao, observacao="Retifica")
    criar_ato_insubsistencia(apostila, observacoes="Anula a apostila")

    atos = auth_client.get(_url()).data[0]["atos_relacionados"]

    for ato in atos:
        assert set(ato) >= CAMPOS_ATO_RELACIONADO
        assert ato["rf"] == "1234567"
        assert ato["data_designacao"] == "2024-01-01"

    insubsistencia_json, apostila_json, cessacao_json = atos

    assert cessacao_json["status"] == "ativo"
    assert cessacao_json["data_cessacao"] == "2024-03-01"
    assert cessacao_json["tipo_insubsistencia"] is None
    assert cessacao_json["tipo_apostila"] is None
    assert cessacao_json["observacoes"] is None

    assert apostila_json["tipo_apostila"] == "CESSACAO"
    assert apostila_json["data_cessacao"] is None
    assert apostila_json["observacoes"] == "Retifica"

    assert insubsistencia_json["tipo_insubsistencia"] == "APOSTILA"
    assert insubsistencia_json["observacoes"] == "Anula a apostila"


@pytest.mark.django_db
def test_ato_relacionado_informa_status_do_pai_desfeito(auth_client):
    """`status` do ato derivado reflete a insubsistência do próprio ato."""
    designacao = criar_ato_designacao(ue=UE)
    cessacao = criar_ato_cessacao(designacao)
    criar_ato_insubsistencia(cessacao)
    AtoAdministrativo.objects.filter(pk=cessacao.pk).update(ativo=False)

    atos = auth_client.get(_url()).data[0]["atos_relacionados"]

    assert atos[1]["status"] == "insubsistente"
    assert atos[1]["ativo"] is False


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
    assert ato["doc"] == "2024-03-02"
    assert ato["portaria"] == "456/2024"
    assert ato["observacoes"] is None


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
        insubsistencia.pk,
        apostila.pk,
        cessacao.pk,
    ]
    assert [ato["tipo"] for ato in atos] == [
        "INSUBSISTENCIA",
        "APOSTILA",
        "CESSACAO",
    ]
    assert [ato["nivel"] for ato in atos] == [3, 2, 1]
    assert [ato["ato_pai_id"] for ato in atos] == [
        apostila.pk,
        cessacao.pk,
        designacao.pk,
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

    insubsistencia_json, apostila_json, cessacao_json = response.data[0][
        "atos_relacionados"
    ]

    assert cessacao_json["tipo_de_ato"] == "Cessação"
    assert cessacao_json["doc"] == "2024-03-01"
    assert cessacao_json["portaria"] == "456/2024"
    assert cessacao_json["nome"] == "Maria Silva"
    assert cessacao_json["observacoes"] is None

    assert apostila_json["tipo_de_ato"] == "Apostila de Cessação"
    assert apostila_json["doc"] == "2024-04-01"
    assert apostila_json["portaria"] == "457/2024"
    assert apostila_json["nome"] == "Maria Silva"
    assert apostila_json["observacoes"] == "Apostila da cessação"

    assert insubsistencia_json["tipo_de_ato"] == "Anulação de Apostila"
    assert insubsistencia_json["doc"] == "2024-05-01"
    assert insubsistencia_json["portaria"] == "458/2024"
    assert insubsistencia_json["nome"] == "Maria Silva"
    assert insubsistencia_json["observacoes"] == "Anulação da apostila"


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
def test_ordem_decrescente_desempata_por_id_e_preserva_ultimo_vigente(
    auth_client,
):
    designacao = criar_ato_designacao(ue=UE)
    primeiro = criar_ato_apostila(designacao)
    segundo = criar_ato_insubsistencia(primeiro)
    terceiro = criar_ato_apostila(designacao)
    AtoAdministrativo.objects.filter(
        pk__in=[primeiro.pk, segundo.pk, terceiro.pk]
    ).update(criado_em=primeiro.criado_em)
    terceiro.ativo = False
    terceiro.save(update_fields=["ativo"])

    response = auth_client.get(_url())

    assert response.status_code == 200
    atos = response.data[0]["atos_relacionados"]
    assert [ato["id"] for ato in atos] == [
        terceiro.pk,
        segundo.pk,
        primeiro.pk,
    ]
    assert [ato["nivel"] for ato in atos] == [1, 2, 1]
    assert [ato["ultimo_ato_vigente"] for ato in atos] == [False, True, False]


@pytest.mark.django_db
def test_historico_rejeita_jwt_invalido():
    client = APIClient()
    client.credentials(HTTP_AUTHORIZATION="Bearer invalido")
    assert client.get(_url()).status_code == 401


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
    assert niveis == [3, 2, 1]


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
def test_descricao_de_cargo_de_vaga_custa_uma_consulta_extra(
    django_assert_num_queries,
):
    """O mapa de cargos é carregado uma única vez, não por designação."""
    cargo, _criado = CargoBase.objects.get_or_create(
        codigo_cargo="9998",
        defaults={
            "descricao_resumida": "Cargo de Teste",
            "descricao_completa": "CARGO DE TESTE",
            "grupamento": CargoBase.Grupamento.GESTORES_EDUCACAO,
            "situacao_funcional": CargoBase.SituacaoFuncional.EFETIVO,
        },
    )
    for indice in range(5):
        criar_ato_designacao(
            ue=UE,
            data_inicio=datetime.date(2020 + indice, 1, 1),
            cargo_vaga=int(cargo.codigo_cargo),
        )

    # 1 consulta da hierarquia + 1 do mapa de cargos, independente do volume.
    with django_assert_num_queries(2):
        designacoes = HistoricoDesignacaoService.listar_por_ue(UE)

    with django_assert_num_queries(0):
        payload = HistoricoDesignacaoSerializer(designacoes, many=True).data

    assert all(
        item["cargo_vaga_display"] == "CARGO DE TESTE" for item in payload
    )


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
