"""Testes dos dados de demonstração do histórico de designações.

Garantem que o seed cobre todos os tipos de ato nas quatro UEs, que é
idempotente, que não toca em designações reais e que os cenários
produzem o resultado esperado no endpoint.
"""

import pytest

from apps.designacao.__tests__.factories import criar_ato_designacao
from apps.designacao.api.serializers.historico_designacao_serializer import (
    HistoricoDesignacaoSerializer,
)
from apps.designacao.models.ato_administrativo import AtoAdministrativo
from apps.designacao.seed.historico_demo import (
    MARCADOR,
    UNIDADES,
    apagar_dados_demo,
    criar_dados_demo,
    dados_existem,
)
from apps.designacao.services.historico_designacao_service import (
    HistoricoDesignacaoService,
)

UE_COMPLETA = "000108"
UE_CESSACOES = "019453"
UE_CADEIA = "093712"
UE_PUBLICACAO = "095432"


def _payload(codigo_ue):
    """Serializa o histórico da UE (mesmo caminho da view)."""
    designacoes = HistoricoDesignacaoService.listar_por_ue(codigo_ue)
    return HistoricoDesignacaoSerializer(designacoes, many=True).data


def _payload_por_portaria(codigo_ue):
    """Indexa o payload pela portaria (ex.: ``"101/2026"``)."""
    return {item["portaria"]: item for item in _payload(codigo_ue)}


# ── Cobertura e idempotência ────────────────────────────────────────────────


@pytest.mark.django_db
def test_cria_designacoes_nas_quatro_ues():
    """Cada uma das quatro UEs recebe designações."""
    dados = criar_dados_demo()

    assert set(dados["por_ue"]) == set(UNIDADES)
    assert all(quantidade > 0 for quantidade in dados["por_ue"].values())
    assert dados["total"] == sum(dados["por_tipo"].values())


@pytest.mark.django_db
def test_cobre_todos_os_tipos_de_ato():
    """Designação, cessação, apostila e insubsistência são criadas."""
    dados = criar_dados_demo()

    for tipo in AtoAdministrativo.Tipo:
        assert dados["por_tipo"][tipo.value] > 0, tipo

    assert dados["por_tipo"]["DESIGNACAO"] == 14
    assert dados["por_tipo"]["CESSACAO"] == 6
    assert dados["por_tipo"]["APOSTILA"] == 7
    assert dados["por_tipo"]["INSUBSISTENCIA"] == 7


@pytest.mark.django_db
def test_seed_e_idempotente():
    """Rodar duas vezes não duplica atos."""
    primeira = criar_dados_demo()
    segunda = criar_dados_demo()

    assert primeira == segunda
    assert (
        AtoAdministrativo.objects.filter(
            sei_numero__startswith=MARCADOR
        ).count()
        == segunda["total"]
    )


@pytest.mark.django_db
def test_apagar_remove_apenas_os_dados_de_demonstracao():
    """A remoção preserva designações reais do banco."""
    real = criar_ato_designacao(ue=UE_COMPLETA)
    criar_dados_demo()

    removidos = apagar_dados_demo()

    assert removidos > 0
    assert not dados_existem()
    assert AtoAdministrativo.objects.filter(pk=real.pk).exists()
    assert len(_payload(UE_COMPLETA)) == 1


@pytest.mark.django_db
def test_apagar_sem_dados_e_no_op():
    """Rodar `--apagar` em banco limpo não quebra."""
    assert apagar_dados_demo() == 0
    assert not dados_existem()


# ── Cenários de vigência ────────────────────────────────────────────────────


@pytest.mark.django_db
def test_ue_completa_tem_arvore_de_quatro_niveis():
    """A designação 101/2026 desce até o 3º nível e fica cessada."""
    criar_dados_demo()

    item = _payload_por_portaria(UE_COMPLETA)["101/2026"]
    assert item["vigente"] is False
    assert item["cessada_em"] == "2026-02-01"
    assert item["status"] == "cessada"

    atos = item["atos_relacionados"]
    assert [ato["nivel"] for ato in atos] == [1, 2, 3]
    assert [ato["tipo_de_ato"] for ato in atos] == [
        "Cessação",
        "Apostila de Cessação",
        "Anulação de Apostila",
    ]
    # Apostila anulada e anulação válida.
    assert [ato["ativo"] for ato in atos] == [True, False, True]


@pytest.mark.django_db
def test_ue_completa_tem_designacao_vigente_e_fora_do_periodo():
    """104/2026 está vigente; 105/2026 expirou pela data_fim."""
    criar_dados_demo()

    itens = _payload_por_portaria(UE_COMPLETA)
    assert itens["104/2026"]["vigente"] is True
    assert itens["104/2026"]["atos_relacionados"] == []

    expirada = itens["105/2026"]
    assert expirada["vigente"] is False
    assert expirada["cessada_em"] is None
    assert expirada["status"] == "ativo"


@pytest.mark.django_db
def test_cessacao_tornada_sem_efeito_devolve_vigencia():
    """201/2026 volta a ficar vigente quando a cessação é insubsistente."""
    criar_dados_demo()

    item = _payload_por_portaria(UE_CESSACOES)["201/2026"]
    assert item["vigente"] is True
    assert item["cessada_em"] is None
    assert item["status"] == "ativo"

    cessacao, insubsistencia = item["atos_relacionados"]
    assert cessacao["tipo_de_ato"] == "Cessação"
    assert cessacao["ativo"] is False
    assert insubsistencia["tipo_de_ato"] == "Insubsistência de Cessação"
    assert insubsistencia["ultimo_ato_vigente"] is True


@pytest.mark.django_db
def test_designacao_com_duas_cessacoes_usa_a_valida():
    """204/2026 tem uma cessação anulada e outra válida."""
    criar_dados_demo()

    item = _payload_por_portaria(UE_CESSACOES)["204/2026"]
    assert item["vigente"] is False
    assert item["cessada_em"] == "2026-06-01"

    ativas = [ato for ato in item["atos_relacionados"] if ato["ativo"]]
    assert [ato["portaria"] for ato in ativas][-1] == "207/2026"


@pytest.mark.django_db
def test_insubsistencia_direta_deixa_designacao_insubsistente():
    """208/2026 é insubstituída sem cessação."""
    criar_dados_demo()

    item = _payload_por_portaria(UE_CESSACOES)["208/2026"]
    assert item["status"] == "insubsistente"
    assert item["vigente"] is False
    assert item["cessada_em"] is None


@pytest.mark.django_db
def test_cadeia_apostila_anulacao_e_tornar_sem_efeito():
    """301/2026 tem apostila, anulação e "Tornar sem efeito"."""
    criar_dados_demo()

    item = _payload_por_portaria(UE_CADEIA)["301/2026"]
    assert item["vigente"] is True

    rotulos = [ato["tipo_de_ato"] for ato in item["atos_relacionados"]]
    assert rotulos == [
        "Apostila de Designação",
        "Anulação de Apostila",
        "Tornar sem efeito",
    ]


@pytest.mark.django_db
def test_ue_de_publicacao_tem_rascunho_e_cessacao_nao_publicada():
    """A UE 095432 mistura atos publicados e não publicados."""
    criar_dados_demo()

    itens = _payload_por_portaria(UE_PUBLICACAO)
    assert itens["401/2026"]["doc"] is None
    assert itens["401/2026"]["vigente"] is True

    # Cessação ainda não publicada, mas ativa: designação cessada.
    cessada = itens["402/2026"]
    assert cessada["vigente"] is False
    assert cessada["cessada_em"] == "2026-09-01"
    assert cessada["atos_relacionados"][0]["tipo_de_ato"] == "Cessação"


# ── Integração com os filtros do endpoint ───────────────────────────────────


@pytest.mark.django_db
def test_seed_responde_a_url_de_filtro_usada_nos_testes_manuais():
    """O cenário criado casa com a query string de exemplo da UE 000108."""
    criar_dados_demo()

    designacoes = HistoricoDesignacaoService.listar_por_ue(
        UE_COMPLETA,
        {
            "status_publicacao": "NAO_PUBLICADO",
            "periodo_after": "2026-10-06",
            "periodo_before": "2026-11-10",
            "observacao": "ssss",
        },
    )

    assert [ato.numero_portaria for ato in designacoes] == [108]


@pytest.mark.django_db
def test_seed_alimenta_o_filtro_de_observacao_em_varias_ues():
    """O texto `ssss` aparece em atos de mais de uma UE."""
    criar_dados_demo()

    for codigo_ue in (UE_COMPLETA, UE_CESSACOES, UE_CADEIA, UE_PUBLICACAO):
        resultado = HistoricoDesignacaoService.listar_por_ue(
            codigo_ue, {"observacao": "ssss"}
        )
        assert resultado, codigo_ue
