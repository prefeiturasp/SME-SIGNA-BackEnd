import pytest
from datetime import date

from apps.designacao.models.ato_administrativo import AtoAdministrativo
from apps.designacao.models.designacao_detalhe import DesignacaoDetalhe
from apps.designacao.models.cessacao_detalhe import CessacaoDetalhe
from apps.designacao.models.insubsistencia_detalhe import InsubsistenciaDetalhe
from apps.designacao.models.apostila_detalhe import ApostilaDetalhe
from apps.designacao.api.serializers.portaria_serializer import PortariaListSerializer


# ─── Helpers ──────────────────────────────────────────────────────────────────


def serialize(ato):
    return PortariaListSerializer(ato).data


# ─── Fixtures base ────────────────────────────────────────────────────────────


@pytest.fixture
def designacao(db):
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


# ─── Testes ───────────────────────────────────────────────────────────────────


@pytest.mark.django_db
class TestPortariaListSerializer:

    # ── Campos básicos ────────────────────────────────────────────────────────

    def test_campos_presentes(self, designacao):
        data = serialize(designacao)
        assert set(data.keys()) == {
            "id",
            "portaria",
            "doc",
            "tipo_de_ato",
            "nome",
            "cargo",
            "data_designacao",
            "data_cessacao",
            "numero_sei",
            "observacoes",
        }

    def test_portaria(self, designacao):
        assert serialize(designacao)["portaria"] == "001/2024"

    def test_doc(self, designacao):
        assert serialize(designacao)["doc"] == "2024-10-23"

    def test_numero_sei(self, designacao):
        assert serialize(designacao)["numero_sei"] == "6018.2024/0001234-5"

    def test_id(self, designacao):
        assert serialize(designacao)["id"] == designacao.pk

    # ── tipo_de_ato ───────────────────────────────────────────────────────────

    def test_tipo_de_ato_designacao(self, designacao):
        assert serialize(designacao)["tipo_de_ato"] == "Designação"

    def test_tipo_de_ato_cessacao(self, cessacao):
        assert serialize(cessacao)["tipo_de_ato"] == "Cessação"

    def test_tipo_de_ato_insubsistencia(self, insubsistencia):
        assert serialize(insubsistencia)["tipo_de_ato"] == "Insubsistência"

    def test_tipo_de_ato_apostila(self, apostila):
        assert serialize(apostila)["tipo_de_ato"] == "Apostila"

    # ── nome ─────────────────────────────────────────────────────────────────

    def test_nome_designacao(self, designacao):
        assert serialize(designacao)["nome"] == "MARIA SILVA"

    def test_nome_usa_nome_civil_quando_servidor_vazio(
        self, designacao_sem_cargo_sobreposto
    ):
        assert serialize(designacao_sem_cargo_sobreposto)["nome"] == "Ana Paula"

    def test_nome_cessacao_herda_da_designacao_pai(self, cessacao, designacao):
        # cessacao.ato_pai = designacao, que tem designacao_detalhe
        ato = AtoAdministrativo.objects.select_related(
            "ato_pai__designacao_detalhe",
            "ato_raiz__designacao_detalhe",
            "cessacao_detalhe",
        ).get(pk=cessacao.pk)
        assert serialize(ato)["nome"] == "MARIA SILVA"

    def test_nome_insubsistencia_herda_da_designacao_pai(
        self, insubsistencia, designacao
    ):
        ato = AtoAdministrativo.objects.select_related(
            "ato_pai__designacao_detalhe",
            "ato_raiz__designacao_detalhe",
            "insubsistencia_detalhe",
        ).get(pk=insubsistencia.pk)
        assert serialize(ato)["nome"] == "MARIA SILVA"

    def test_nome_apostila_herda_da_designacao_pai(self, apostila, designacao):
        ato = AtoAdministrativo.objects.select_related(
            "ato_pai__designacao_detalhe",
            "ato_raiz__designacao_detalhe",
            "apostila_detalhe",
        ).get(pk=apostila.pk)
        assert serialize(ato)["nome"] == "MARIA SILVA"

    # ── cargo ─────────────────────────────────────────────────────────────────

    def test_cargo_usa_sobreposto(self, designacao):
        assert serialize(designacao)["cargo"] == "DIRETOR DE ESCOLA"

    def test_cargo_usa_base_quando_sobreposto_vazio(
        self, designacao_sem_cargo_sobreposto
    ):
        assert (
            serialize(designacao_sem_cargo_sobreposto)["cargo"] == "PROFESSOR DE EF II"
        )

    # ── data_designacao ───────────────────────────────────────────────────────

    def test_data_designacao(self, designacao):
        assert serialize(designacao)["data_designacao"] == date(2024, 1, 15)

    def test_data_designacao_cessacao_herda_do_pai(self, cessacao, designacao):
        ato = AtoAdministrativo.objects.select_related(
            "ato_pai__designacao_detalhe",
            "ato_raiz__designacao_detalhe",
        ).get(pk=cessacao.pk)
        assert serialize(ato)["data_designacao"] == date(2024, 1, 15)

    # ── data_cessacao ─────────────────────────────────────────────────────────

    def test_data_cessacao_em_ato_cessacao(self, cessacao):
        ato = AtoAdministrativo.objects.select_related("cessacao_detalhe").get(
            pk=cessacao.pk
        )
        assert serialize(ato)["data_cessacao"] == date(2024, 6, 30)

    def test_data_cessacao_designacao_sem_data_fim(self, designacao):
        ato = AtoAdministrativo.objects.select_related("designacao_detalhe").get(
            pk=designacao.pk
        )
        assert serialize(ato)["data_cessacao"] is None

    def test_data_cessacao_designacao_com_data_fim(self, designacao_com_data_fim):
        ato = AtoAdministrativo.objects.select_related("designacao_detalhe").get(
            pk=designacao_com_data_fim.pk
        )
        assert serialize(ato)["data_cessacao"] == date(2024, 12, 31)

    def test_data_cessacao_insubsistencia_retorna_none(self, insubsistencia):
        ato = AtoAdministrativo.objects.select_related(
            "ato_pai__designacao_detalhe",
            "insubsistencia_detalhe",
        ).get(pk=insubsistencia.pk)
        assert serialize(ato)["data_cessacao"] is None

    # ── observacoes ───────────────────────────────────────────────────────────

    def test_observacoes_designacao_retorna_none(self, designacao):
        assert serialize(designacao)["observacoes"] is None

    def test_observacoes_cessacao_retorna_none(self, cessacao):
        ato = AtoAdministrativo.objects.select_related("cessacao_detalhe").get(
            pk=cessacao.pk
        )
        assert serialize(ato)["observacoes"] is None

    def test_observacoes_insubsistencia(self, insubsistencia):
        ato = AtoAdministrativo.objects.select_related("insubsistencia_detalhe").get(
            pk=insubsistencia.pk
        )
        assert serialize(ato)["observacoes"] == "Portaria revogada por erro material."

    def test_observacoes_insubsistencia_vazia(self, insubsistencia_sem_observacoes):
        ato = AtoAdministrativo.objects.select_related("insubsistencia_detalhe").get(
            pk=insubsistencia_sem_observacoes.pk
        )
        assert serialize(ato)["observacoes"] == ""

    def test_observacoes_apostila(self, apostila):
        ato = AtoAdministrativo.objects.select_related("apostila_detalhe").get(
            pk=apostila.pk
        )
        assert serialize(ato)["observacoes"] == "Apostila de retificacao de cargo."
