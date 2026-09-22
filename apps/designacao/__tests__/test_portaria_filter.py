"""Testes para filtro de portaria."""

from datetime import date

import pytest

from apps.designacao.api.filters.portaria_filter import PortariaFilter
from apps.designacao.models.ato_administrativo import AtoAdministrativo
from apps.designacao.models.cessacao_detalhe import CessacaoDetalhe
from apps.designacao.models.designacao_detalhe import DesignacaoDetalhe

# ─── Helper ───────────────────────────────────────────────────────────────────


def apply_filter(params):
    """Método apply filter."""
    qs = AtoAdministrativo.objects.all()
    f = PortariaFilter(data=params, queryset=qs)
    return f.qs


# ─── Fixtures ─────────────────────────────────────────────────────────────────


@pytest.fixture
def designacao_1(db):
    """Método designacao 1."""
    ato = AtoAdministrativo.objects.create(
        tipo="DESIGNACAO",
        numero_portaria=1,
        ano_vigente="2024",
        sei_numero="6018.2024/0001234-5",
        doc=None,
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
    """Método designacao 2."""
    ato = AtoAdministrativo.objects.create(
        tipo="DESIGNACAO",
        numero_portaria=2,
        ano_vigente="2024",
        sei_numero="6018.2024/0002345-6",
        doc=None,
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
    """Método cessacao."""
    ato = AtoAdministrativo.objects.create(
        tipo="CESSACAO",
        numero_portaria=3,
        ano_vigente="2024",
        sei_numero="6018.2024/0003456-7",
        doc=None,
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
    """Método insubsistencia."""
    return AtoAdministrativo.objects.create(
        tipo="INSUBSISTENCIA",
        numero_portaria=4,
        ano_vigente="2024",
        sei_numero="6018.2024/0004567-8",
        doc=None,
        ativo=True,
        ato_pai=designacao_1,
    )


# ─── Testes ───────────────────────────────────────────────────────────────────


@pytest.mark.django_db
class TestPortariaFilter:

    # tipo
    """Testes para portaria filter."""

    def test_filtro_tipo_designacao(
        self, designacao_1, designacao_2, cessacao
    ):
        """Verifica filtro tipo designacao."""
        qs = apply_filter({"tipo": "DESIGNACAO"})
        assert all(a.tipo == "DESIGNACAO" for a in qs)
        assert qs.count() == 2

    def test_filtro_tipo_cessacao(self, designacao_1, cessacao):
        """Verifica filtro tipo cessacao."""
        qs = apply_filter({"tipo": "CESSACAO"})
        assert qs.count() == 1
        assert qs.first() == cessacao

    def test_filtro_tipo_insubsistencia(
        self, designacao_1, cessacao, insubsistencia
    ):
        """Verifica filtro tipo insubsistencia."""
        qs = apply_filter({"tipo": "INSUBSISTENCIA"})
        assert qs.count() == 1
        assert qs.first() == insubsistencia

    # DESIGNACAO_CESSACAO
    def test_filtro_tipo_designacao_cessacao_retorna_ambos(
        self, designacao_1, designacao_2, cessacao, insubsistencia
    ):
        """Verifica filtro tipo designacao cessacao retorna ambos."""
        qs = apply_filter({"tipo": "DESIGNACAO_CESSACAO"})
        tipos = set(qs.values_list("tipo", flat=True))
        assert tipos == {"DESIGNACAO", "CESSACAO"}

    def test_filtro_tipo_designacao_cessacao_nao_retorna_insubsistencia(
        self, designacao_1, cessacao, insubsistencia
    ):
        """Verifica filtro tipo designacao cessacao nao retorna insubsistencia."""
        qs = apply_filter({"tipo": "DESIGNACAO_CESSACAO"})
        assert not qs.filter(tipo="INSUBSISTENCIA").exists()

    def test_filtro_tipo_designacao_cessacao_quantidade(
        self, designacao_1, designacao_2, cessacao, insubsistencia
    ):
        """Verifica filtro tipo designacao cessacao quantidade."""
        qs = apply_filter({"tipo": "DESIGNACAO_CESSACAO"})
        # 2 designações + 1 cessação = 3
        assert qs.count() == 3

    def test_filtro_tipo_designacao_cessacao_sem_cessacoes(
        self, designacao_1, designacao_2
    ):
        """Verifica filtro tipo designacao cessacao sem cessacoes."""
        qs = apply_filter({"tipo": "DESIGNACAO_CESSACAO"})
        assert qs.count() == 2
        assert all(a.tipo == "DESIGNACAO" for a in qs)

    def test_filtro_tipo_designacao_cessacao_sem_designacoes(
        self, designacao_1, cessacao
    ):
        # Filtra apenas cessação no queryset
        """Verifica filtro tipo designacao cessacao sem designacoes."""
        qs = AtoAdministrativo.objects.filter(tipo="CESSACAO")
        f = PortariaFilter(data={"tipo": "DESIGNACAO_CESSACAO"}, queryset=qs)
        assert f.qs.count() == 1
        assert f.qs.first().tipo == "CESSACAO"


# ─── Intervalo numérico ───────────────────────────────────────────────────────


@pytest.fixture
def portarias_99_e_100(db):
    """Cria duas portarias que expõem comparação lexicográfica.

    Em texto "100" < "99", então um filtro de intervalo que compare como
    string devolve o conjunto errado para esses dois valores.
    """
    for numero in (99, 100):
        AtoAdministrativo.objects.create(
            tipo="DESIGNACAO",
            numero_portaria=numero,
            ano_vigente="2024",
            sei_numero=f"6018.2024/000{numero}-0",
            doc=None,
            ativo=True,
        )


@pytest.mark.django_db
class TestPortariaFilterIntervaloNumerico:
    """Garante que o intervalo de portaria compare números, não texto."""

    def test_portaria_inicial_inclui_numero_maior_que_dois_digitos(
        self, portarias_99_e_100
    ):
        """Verifica que 100 entra no intervalo que começa em 99."""
        qs = apply_filter({"portaria_inicial": "99"})
        assert set(qs.values_list("numero_portaria", flat=True)) == {99, 100}

    def test_portaria_final_exclui_numero_maior(self, portarias_99_e_100):
        """Verifica que 100 fica fora do intervalo que termina em 99."""
        qs = apply_filter({"portaria_final": "99"})
        assert list(qs.values_list("numero_portaria", flat=True)) == [99]

    def test_intervalo_fechado_isola_a_portaria(self, portarias_99_e_100):
        """Verifica intervalo fechado de 100 a 100."""
        qs = apply_filter({"portaria_inicial": "100", "portaria_final": "100"})
        assert list(qs.values_list("numero_portaria", flat=True)) == [100]

    def test_apostila_sem_numero_fica_fora_do_intervalo(
        self, portarias_99_e_100, designacao_1
    ):
        """Verifica que ato sem número de portaria não entra no intervalo."""
        AtoAdministrativo.objects.create(
            tipo="APOSTILA",
            ato_pai=designacao_1,
            numero_portaria=None,
            ano_vigente="",
            sei_numero="6018.2024/0000999-9",
            doc=None,
            ativo=True,
        )
        qs = apply_filter({"portaria_inicial": "1"})
        assert not qs.filter(numero_portaria=None).exists()

    def test_ordenacao_por_numero_e_numerica(self, portarias_99_e_100):
        """Verifica que a ordenação coloca 99 antes de 100."""
        qs = AtoAdministrativo.objects.order_by("numero_portaria")
        assert list(qs.values_list("numero_portaria", flat=True)) == [99, 100]
