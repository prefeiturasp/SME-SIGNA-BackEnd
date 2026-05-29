"""Testes unitários para o serializer de portaria.

Este módulo valida a serialização de portarias de atos administrativos,
incluindo designações, cess ações, insubsistências e apostilas.
"""

from datetime import date

import pytest

from apps.designacao.api.serializers.portaria_serializer import (
    PortariaListSerializer,
)
from apps.designacao.models.apostila_detalhe import ApostilaDetalhe
from apps.designacao.models.ato_administrativo import AtoAdministrativo
from apps.designacao.models.cessacao_detalhe import CessacaoDetalhe
from apps.designacao.models.designacao_detalhe import DesignacaoDetalhe
from apps.designacao.models.insubsistencia_detalhe import InsubsistenciaDetalhe


# ─── Helpers ──────────────────────────────────────────────────────────────────


def serialize(ato):
    """Serializa um ato administrativo para dados de portaria.

    Args:
        ato: Instância de AtoAdministrativo a ser serializada.

    Returns:
        dict: Dados serializados do ato administrativo.
    """
    return PortariaListSerializer(ato).data


# ─── Constantes ────────────────────────────────────────────────────────────


DADOS_CESSACAO = {
            "portaria": "002/2024", 
            "ano_vigente": "2024", 
            "numero_sei": "6018.2024/0002345-6", 
            "doc": date(2024, 10, 24), 
            "remocao": False, 
            "a_pedido": False, 
            "aposentadoria": False, 
            "data_cessacao": date(2024, 6, 30)
}

DADOS_DESIGNACAO = {
             "portaria": "001/2024",
             "ano_vigente": "2024",
             "numero_sei": "6018.2024/0001234-5",
             "doc": date(2024, 10, 23),
             "dre_nome": "DRE BUTANTA",
             "indicado_rf": "12345678",
             "indicado_vinculo": 1,
             "indicado_nome_civil": "Maria da Silva",
             "indicado_nome_servidor": "MARIA SILVA",
             "indicado_lotacao": "EMEF TESTE 1",
             "indicado_cargo_base": "PROFESSOR DE EF I",
             "indicado_cargo_sobreposto": "DIRETOR DE ESCOLA",
             "indicado_local_exercicio": "EMEF TESTE 1",
             "tipo_vaga": "VAGO",
             "titular_nome_civil": "",
             "titular_nome_servidor": "",
             "titular_rf": "",
             "titular_cargo_base": "",
             "titular_vinculo": None,
             "titular_tipo_vinculo": "Nao encontrado",
             "impedimento_substituicao": None,
             "ue": "",
             "codigo_hierarquico": "108600",
             "data_inicio": date(2024, 1, 15),
             "data_fim": None
}



# ─── Fixtures base ────────────────────────────────────────────────────────────


@pytest.fixture
def designacao(db):
    """Método designacao."""
    ato = AtoAdministrativo.objects.create(
        tipo="DESIGNACAO",
        numero_portaria="001/2024",
        ano_vigente="2024",
        sei_numero="6018.2024/0001234-5",
        doc="2024-10-23",
        ativo=True,
    )
    DesignacaoDetalhe.objects.create(
        ato=ato,
        dre_nome="DRE BUTANTA",
        unidade_proponente="EMEF TESTE 1",
        codigo_hierarquico="108600",
        indicado_nome_servidor="MARIA SILVA",
        indicado_nome_civil="Maria da Silva",
        indicado_rf="12345678",
        indicado_vinculo=1,
        indicado_cargo_base="PROFESSOR DE EF I",
        indicado_lotacao="EMEF TESTE 1",
        indicado_cargo_sobreposto="DIRETOR DE ESCOLA",
        indicado_codigo_cargo_sobreposto=3360,
        indicado_local_exercicio="EMEF TESTE 1",
        data_inicio=date(2024, 1, 15),
        data_fim=None,
        tipo_vaga="VAGO",
        cargo_vaga=3360,
    )
    return ato


@pytest.fixture
def designacao_com_data_fim(db):
    """Método designacao com data fim."""
    ato = AtoAdministrativo.objects.create(
        tipo="DESIGNACAO",
        numero_portaria="005/2024",
        ano_vigente="2024",
        sei_numero="6018.2024/0005678-9",
        doc=None,
        ativo=True,
    )
    DesignacaoDetalhe.objects.create(
        ato=ato,
        dre_nome="DRE LAPA",
        unidade_proponente="EMEF TESTE 5",
        codigo_hierarquico="108900",
        indicado_nome_servidor="CARLOS LIMA",
        indicado_nome_civil="Carlos Lima",
        indicado_rf="11223344",
        indicado_vinculo=1,
        indicado_cargo_base="PROFESSOR DE EF I",
        indicado_lotacao="EMEF TESTE 5",
        indicado_cargo_sobreposto="",
        indicado_local_exercicio="EMEF TESTE 5",
        data_inicio=date(2024, 1, 1),
        data_fim=date(2024, 12, 31),
        tipo_vaga="VAGO",
        cargo_vaga=3360,
    )
    return ato


@pytest.fixture
def designacao_sem_cargo_sobreposto(db):
    """Método designacao sem cargo sobreposto."""
    ato = AtoAdministrativo.objects.create(
        tipo="DESIGNACAO",
        numero_portaria="006/2024",
        ano_vigente="2024",
        sei_numero="6018.2024/0006789-0",
        doc=None,
        ativo=True,
    )
    DesignacaoDetalhe.objects.create(
        ato=ato,
        dre_nome="DRE MOOCA",
        unidade_proponente="EMEF TESTE 6",
        codigo_hierarquico="109000",
        indicado_nome_servidor="",
        indicado_nome_civil="Ana Paula",
        indicado_rf="55667788",
        indicado_vinculo=1,
        indicado_cargo_base="PROFESSOR DE EF II",
        indicado_lotacao="EMEF TESTE 6",
        indicado_cargo_sobreposto="",
        indicado_local_exercicio="EMEF TESTE 6",
        data_inicio=date(2024, 3, 1),
        tipo_vaga="DISPONIVEL",
        cargo_vaga=3379,
    )
    return ato


@pytest.fixture
def cessacao(db, designacao):
    """Método cessacao."""
    ato = AtoAdministrativo.objects.create(
        tipo="CESSACAO",
        numero_portaria="002/2024",
        ano_vigente="2024",
        sei_numero="6018.2024/0002345-6",
        doc="2024-10-24",
        ativo=True,
        ato_pai=designacao,
    )
    CessacaoDetalhe.objects.create(
        ato=ato,
        data_cessacao=date(2024, 6, 30),
    )
    return ato


@pytest.fixture
def insubsistencia(db, designacao):
    """Método insubsistencia."""
    ato = AtoAdministrativo.objects.create(
        tipo="INSUBSISTENCIA",
        numero_portaria="003/2024",
        ano_vigente="2024",
        sei_numero="6018.2024/0003456-7",
        doc=None,
        ativo=True,
        ato_pai=designacao,
    )
    InsubsistenciaDetalhe.objects.create(
        ato=ato,
        observacoes="Portaria revogada por erro material.",
    )
    return ato


@pytest.fixture
def insubsistencia_sem_observacoes(db, designacao):
    """Método insubsistencia sem observacoes."""
    ato = AtoAdministrativo.objects.create(
        tipo="INSUBSISTENCIA",
        numero_portaria="007/2024",
        ano_vigente="2024",
        sei_numero="6018.2024/0007890-1",
        doc=None,
        ativo=True,
        ato_pai=designacao,
    )
    InsubsistenciaDetalhe.objects.create(ato=ato, observacoes="")
    return ato

@pytest.fixture
def apostila(db, designacao):
    """Método apostila."""
    ato = AtoAdministrativo.objects.create(
        tipo="APOSTILA",
        numero_portaria="004/2024",
        ano_vigente="2024",
        sei_numero="6018.2024/0004567-8",
        doc=None,
        ativo=True,
        ato_pai=designacao,
    )
    ApostilaDetalhe.objects.create(
        ato=ato,
        observacao="Apostila de retificacao de cargo.",
    )
    return ato


@pytest.fixture
def apostila_cessacao(db, cessacao):
    """Método apostila."""
    ato = AtoAdministrativo.objects.create(
        tipo="APOSTILA",
        numero_portaria="005/2024",
        ano_vigente="2024",
        sei_numero="6019.2024/0004567-8",
        doc=None,
        ativo=True,
        ato_pai=cessacao,
    )
    ApostilaDetalhe.objects.create(
        ato=ato,
        observacao="Apostila de retificacao de cessação.",
    )
    return ato


# ─── Testes ───────────────────────────────────────────────────────────────────


@pytest.mark.django_db
class TestPortariaListSerializer:
    """Testa a serialização de listas de portarias.

    Verifica campos básicos, tipos de ato, dados de servidor, datas e observações
    retornadas pelo serializer de portaria.
    """

    # ── Campos básicos ────────────────────────────────────────────────────────
    def test_campos_presentes(self, designacao):
        """Verifica campos presentes."""
        data = serialize(designacao)
        assert set(data.keys()) == {
            "id",
            "portaria",
            "doc",
            "ano",
            "tipo_de_ato",
            "nome",
            "cargo",
            "data_designacao",
            "data_cessacao",
            "numero_sei",
            "observacoes",
            "designacao",
            "cessacao",
            "tipo_insubsistencia",
            "tipo_apostila",
            "tipo"
        }
       
    def test_designacao(self, designacao):
        """Verifica designacao."""        
        assert serialize(designacao)["designacao"] == DADOS_DESIGNACAO

    def test_cessacao(self, cessacao):
        """Verifica cessacao."""                
        assert serialize(cessacao)["cessacao"] == DADOS_CESSACAO
 
    def test_desinacao_de_apostila_designacao(self, apostila):
        """Verifica tipo de ato apostila."""
        assert serialize(apostila)["designacao"] == DADOS_DESIGNACAO

    def test_desinacao_de_apostila_cessacao(self, apostila_cessacao):
        """Verifica tipo de ato apostila_cessacao."""
        assert serialize(apostila_cessacao)["cessacao"] == DADOS_CESSACAO

    def test_portaria(self, designacao):
        """Verifica portaria."""
        assert serialize(designacao)["portaria"] == "001/2024"

    def test_doc(self, designacao):
        """Verifica data DO."""
        assert serialize(designacao)["doc"] == "2024-10-23"

    def test_numero_sei(self, designacao):
        """Verifica numero sei."""
        assert serialize(designacao)["numero_sei"] == "6018.2024/0001234-5"

    def test_id(self, designacao):
        """Verifica id."""
        assert serialize(designacao)["id"] == designacao.pk

    # ── tipo_de_ato ───────────────────────────────────────────────────────────

    def test_tipo_de_ato_designacao(self, designacao):
        """Verifica tipo de ato designacao."""
        assert serialize(designacao)["tipo_de_ato"] == "Designação"

    def test_tipo_de_ato_cessacao(self, cessacao):
        """Verifica tipo de ato cessacao."""
        assert serialize(cessacao)["tipo_de_ato"] == "Cessação"

    def test_tipo_de_ato_insubsistencia(self, insubsistencia):
        """Verifica tipo de ato insubsistencia."""
        assert serialize(insubsistencia)["tipo_de_ato"] == "Insubsistência"

    def test_tipo_de_ato_apostila(self, apostila):
        """Verifica tipo de ato apostila."""
        assert serialize(apostila)["tipo_de_ato"] == "Apostila"

    # ── tipo_de_ato ───────────────────────────────────────────────────────────

    def test_tipo_de_designacao(self, designacao):
        """Verifica tipo de ato designacao."""
        assert serialize(designacao)["tipo"] == "DESIGNACAO"

    def test_tipo_de_cessacao(self, cessacao):
        """Verifica tipo de ato cessacao."""
        assert serialize(cessacao)["tipo"] == "CESSACAO"

    def test_tipo_de_insubsistencia(self, insubsistencia):
        """Verifica tipo de ato insubsistencia."""
        assert serialize(insubsistencia)["tipo"] == "INSUBSISTENCIA"

    def test_tipo_de_apostila(self, apostila):
        """Verifica tipo de ato apostila."""
        assert serialize(apostila)["tipo"] == "APOSTILA"

    # ── nome ─────────────────────────────────────────────────────────────────

    def test_nome_designacao(self, designacao):
        """Verifica nome designacao."""
        assert serialize(designacao)["nome"] == "MARIA SILVA"

    def test_nome_usa_nome_civil_quando_servidor_vazio(
        self, designacao_sem_cargo_sobreposto
    ):
        """Verifica nome usa nome civil quando servidor vazio."""
        assert (
            serialize(designacao_sem_cargo_sobreposto)["nome"] == "Ana Paula"
        )

    def test_nome_cessacao_herda_da_designacao_pai(self, cessacao, designacao):
        # cessacao.ato_pai = designacao, que tem designacao_detalhe
        """Verifica nome cessacao herda da designacao pai."""
        ato = AtoAdministrativo.objects.select_related(
            "ato_pai__designacao_detalhe",
            "ato_raiz__designacao_detalhe",
            "cessacao_detalhe",
        ).get(pk=cessacao.pk)
        assert serialize(ato)["nome"] == "MARIA SILVA"

    def test_nome_insubsistencia_herda_da_designacao_pai(
        self, insubsistencia, designacao
    ):
        """Verifica nome insubsistencia herda da designacao pai."""
        ato = AtoAdministrativo.objects.select_related(
            "ato_pai__designacao_detalhe",
            "ato_raiz__designacao_detalhe",
            "insubsistencia_detalhe",
        ).get(pk=insubsistencia.pk)
        assert serialize(ato)["nome"] == "MARIA SILVA"

    def test_nome_apostila_herda_da_designacao_pai(self, apostila, designacao):
        """Verifica nome apostila herda da designacao pai."""
        ato = AtoAdministrativo.objects.select_related(
            "ato_pai__designacao_detalhe",
            "ato_raiz__designacao_detalhe",
            "apostila_detalhe",
        ).get(pk=apostila.pk)
        assert serialize(ato)["nome"] == "MARIA SILVA"

    # ── cargo ─────────────────────────────────────────────────────────────────

    def test_cargo_usa_sobreposto(self, designacao):
        """Verifica cargo usa sobreposto."""
        assert serialize(designacao)["cargo"] == "DIRETOR DE ESCOLA"

    def test_cargo_usa_base_quando_sobreposto_vazio(
        self, designacao_sem_cargo_sobreposto
    ):
        """Verifica cargo usa base quando sobreposto vazio."""
        assert (
            serialize(designacao_sem_cargo_sobreposto)["cargo"]
            == "PROFESSOR DE EF II"
        )

    # ── data_designacao ───────────────────────────────────────────────────────

    def test_data_designacao(self, designacao):
        """Verifica data designacao."""
        assert serialize(designacao)["data_designacao"] == date(2024, 1, 15)

    def test_data_designacao_cessacao_herda_do_pai(self, cessacao, designacao):
        """Verifica data designacao cessacao herda do pai."""
        ato = AtoAdministrativo.objects.select_related(
            "ato_pai__designacao_detalhe",
            "ato_raiz__designacao_detalhe",
        ).get(pk=cessacao.pk)
        assert serialize(ato)["data_designacao"] == date(2024, 1, 15)

    # ── data_cessacao ─────────────────────────────────────────────────────────

    def test_data_cessacao_em_ato_cessacao(self, cessacao):
        """Verifica data cessacao em ato cessacao."""
        ato = AtoAdministrativo.objects.select_related("cessacao_detalhe").get(
            pk=cessacao.pk
        )
        assert serialize(ato)["data_cessacao"] == date(2024, 6, 30)

    def test_data_cessacao_designacao_sem_data_fim(self, designacao):
        """Verifica data cessacao designacao sem data fim."""
        ato = AtoAdministrativo.objects.select_related(
            "designacao_detalhe"
        ).get(pk=designacao.pk)
        assert serialize(ato)["data_cessacao"] is None

    def test_data_cessacao_designacao_com_data_fim(
        self, designacao_com_data_fim
    ):
        """Verifica data cessacao designacao com data fim."""
        ato = AtoAdministrativo.objects.select_related(
            "designacao_detalhe"
        ).get(pk=designacao_com_data_fim.pk)
        assert serialize(ato)["data_cessacao"] == date(2024, 12, 31)

    def test_data_cessacao_insubsistencia_retorna_none(self, insubsistencia):
        """Verifica data cessacao insubsistencia retorna none."""
        ato = AtoAdministrativo.objects.select_related(
            "ato_pai__designacao_detalhe",
            "insubsistencia_detalhe",
        ).get(pk=insubsistencia.pk)
        assert serialize(ato)["data_cessacao"] is None

    # ── observacoes ───────────────────────────────────────────────────────────

    def test_observacoes_designacao_retorna_none(self, designacao):
        """Verifica observacoes designacao retorna none."""
        assert serialize(designacao)["observacoes"] is None

    def test_observacoes_cessacao_retorna_none(self, cessacao):
        """Verifica observacoes cessacao retorna none."""
        ato = AtoAdministrativo.objects.select_related("cessacao_detalhe").get(
            pk=cessacao.pk
        )
        assert serialize(ato)["observacoes"] is None

    def test_observacoes_insubsistencia(self, insubsistencia):
        """Verifica observacoes insubsistencia."""
        ato = AtoAdministrativo.objects.select_related(
            "insubsistencia_detalhe"
        ).get(pk=insubsistencia.pk)
        assert (
            serialize(ato)["observacoes"]
            == "Portaria revogada por erro material."
        )

    def test_observacoes_insubsistencia_vazia(
        self, insubsistencia_sem_observacoes
    ):
        """Verifica observacoes insubsistencia vazia."""
        ato = AtoAdministrativo.objects.select_related(
            "insubsistencia_detalhe"
        ).get(pk=insubsistencia_sem_observacoes.pk)
        assert serialize(ato)["observacoes"] == ""

    def test_observacoes_apostila(self, apostila):
        """Verifica observacoes apostila."""
        ato = AtoAdministrativo.objects.select_related("apostila_detalhe").get(
            pk=apostila.pk
        )
        assert (
            serialize(ato)["observacoes"]
            == "Apostila de retificacao de cargo."
        )
