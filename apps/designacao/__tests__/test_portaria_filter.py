from datetime import date

import pytest

from apps.designacao.api.filters.portaria_filter import PortariaFilter
from apps.designacao.models.ato_administrativo import AtoAdministrativo
from apps.designacao.models.cessacao_detalhe import CessacaoDetalhe
from apps.designacao.models.designacao_detalhe import DesignacaoDetalhe

# ─── Helper ───────────────────────────────────────────────────────────────────


def apply_filter(params):
    qs = AtoAdministrativo.objects.all()
    f = PortariaFilter(data=params, queryset=qs)
    return f.qs


# ─── Fixtures ─────────────────────────────────────────────────────────────────


@pytest.fixture
def designacao_1(db):
    ato = AtoAdministrativo.objects.create(
        tipo="DESIGNACAO",
        numero_portaria="001/2024",
        ano_vigente="2024",
        sei_numero="6018.2024/0001234-5",
        doc="",
        ativo=True,
    )
    DesignacaoDetalhe.objects.create(
        ato=ato,
        dre_nome="DRE BUTANTA",  # sem acento para evitar falha de collation
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
        tipo_vaga="VAGO",
        cargo_vaga=3360,
    )
    return ato


@pytest.fixture
def designacao_2(db):
    ato = AtoAdministrativo.objects.create(
        tipo="DESIGNACAO",
        numero_portaria="002/2024",
        ano_vigente="2024",
        sei_numero="6018.2024/0002345-6",
        doc="",
        ativo=True,
    )
    DesignacaoDetalhe.objects.create(
        ato=ato,
        dre_nome="DRE IPIRANGA",
        unidade_proponente="EMEF TESTE 2",
        codigo_hierarquico="108700",
        indicado_nome_servidor="JOAO SOUZA",
        indicado_nome_civil="Joao de Souza",
        indicado_rf="87654321",
        indicado_vinculo=1,
        indicado_cargo_base="PROFESSOR DE EF II",
        indicado_lotacao="EMEF TESTE 2",
        indicado_cargo_sobreposto="COORDENADOR PEDAGOGICO",
        indicado_codigo_cargo_sobreposto=3379,
        indicado_local_exercicio="EMEF TESTE 2",
        data_inicio=date(2024, 2, 1),
        tipo_vaga="DISPONIVEL",
        cargo_vaga=3379,
    )
    return ato


@pytest.fixture
def cessacao(db, designacao_1):
    # CESSACAO obrigatoriamente precisa de ato_pai do tipo DESIGNACAO
    ato = AtoAdministrativo.objects.create(
        tipo="CESSACAO",
        numero_portaria="003/2024",
        ano_vigente="2024",
        sei_numero="6018.2024/0003456-7",
        doc="",
        ativo=True,
        ato_pai=designacao_1,
    )
    CessacaoDetalhe.objects.create(
        ato=ato,
        data_cessacao=date(2024, 6, 30),
    )
    return ato


@pytest.fixture
def insubsistencia(db, designacao_1):
    # INSUBSISTENCIA também precisa de ato_pai
    return AtoAdministrativo.objects.create(
        tipo="INSUBSISTENCIA",
        numero_portaria="004/2024",
        ano_vigente="2024",
        sei_numero="6018.2024/0004567-8",
        doc="",
        ativo=True,
        ato_pai=designacao_1,
    )


# ─── Testes ───────────────────────────────────────────────────────────────────


@pytest.mark.django_db
class TestPortariaFilter:

    # tipo
    def test_filtro_tipo_designacao(
        self, designacao_1, designacao_2, cessacao
    ):
        qs = apply_filter({"tipo": "DESIGNACAO"})
        assert all(a.tipo == "DESIGNACAO" for a in qs)
        assert qs.count() == 2

    def test_filtro_tipo_cessacao(self, designacao_1, cessacao):
        qs = apply_filter({"tipo": "CESSACAO"})
        assert qs.count() == 1
        assert qs.first() == cessacao

    def test_filtro_tipo_insubsistencia(
        self, designacao_1, cessacao, insubsistencia
    ):
        qs = apply_filter({"tipo": "INSUBSISTENCIA"})
        assert qs.count() == 1
        assert qs.first() == insubsistencia

    # DESIGNACAO_CESSACAO
    def test_filtro_tipo_designacao_cessacao_retorna_ambos(
        self, designacao_1, designacao_2, cessacao, insubsistencia
    ):
        qs = apply_filter({"tipo": "DESIGNACAO_CESSACAO"})
        tipos = set(qs.values_list("tipo", flat=True))
        assert tipos == {"DESIGNACAO", "CESSACAO"}

    def test_filtro_tipo_designacao_cessacao_nao_retorna_insubsistencia(
        self, designacao_1, cessacao, insubsistencia
    ):
        qs = apply_filter({"tipo": "DESIGNACAO_CESSACAO"})
        assert not qs.filter(tipo="INSUBSISTENCIA").exists()

    def test_filtro_tipo_designacao_cessacao_quantidade(
        self, designacao_1, designacao_2, cessacao, insubsistencia
    ):
        qs = apply_filter({"tipo": "DESIGNACAO_CESSACAO"})
        # 2 designações + 1 cessação = 3
        assert qs.count() == 3

    def test_filtro_tipo_designacao_cessacao_sem_cessacoes(
        self, designacao_1, designacao_2
    ):
        qs = apply_filter({"tipo": "DESIGNACAO_CESSACAO"})
        assert qs.count() == 2
        assert all(a.tipo == "DESIGNACAO" for a in qs)

    def test_filtro_tipo_designacao_cessacao_sem_designacoes(
        self, designacao_1, cessacao
    ):
        # Filtra apenas cessação no queryset
        qs = AtoAdministrativo.objects.filter(tipo="CESSACAO")
        f = PortariaFilter(data={"tipo": "DESIGNACAO_CESSACAO"}, queryset=qs)
        assert f.qs.count() == 1
        assert f.qs.first().tipo == "CESSACAO"
