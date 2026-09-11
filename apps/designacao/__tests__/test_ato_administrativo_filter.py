"""Testes para filtro de atos administrativos."""

import datetime
from datetime import date

import pytest

from apps.designacao.api.filters.ato_administrativo_filter import (
    AtoAdministrativoFilter,
)
from apps.designacao.models.apostila_detalhe import ApostilaDetalhe
from apps.designacao.models.ato_administrativo import AtoAdministrativo
from apps.designacao.models.cessacao_detalhe import CessacaoDetalhe
from apps.designacao.models.designacao_detalhe import DesignacaoDetalhe
from apps.designacao.models.insubsistencia_detalhe import InsubsistenciaDetalhe

# ─── Helper ───────────────────────────────────────────────────────────────────


def apply_filter(params):
    """Método apply filter."""
    qs = AtoAdministrativo.objects.all()
    f = AtoAdministrativoFilter(data=params, queryset=qs)
    return f.qs


# ─── Fixtures ─────────────────────────────────────────────────────────────────


@pytest.fixture
def designacao_1(db):
    """Método designacao 1."""
    ato = AtoAdministrativo.objects.create(
        tipo="DESIGNACAO",
        numero_portaria="001/2024",
        ano_vigente="2024",
        sei_numero="6018.2024/0001234-5",
        doc=None,
        ativo=True,
        status_publicacao=AtoAdministrativo.StatusPublicacao.NAO_PUBLICADO,
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
        tipo_vaga="DISPONIVEL",
        cargo_vaga=3360,
        titular_nome_servidor="Joao de Souza",
        titular_nome_civil="Joao de Souza",
        titular_rf="12345678",
        titular_vinculo=1,
        titular_cargo_base="PROFESSOR DE EF I",
        titular_lotacao="EMEF TESTE 1",
        titular_cargo_sobreposto="DIRETOR DE ESCOLA",
        titular_codigo_cargo_sobreposto=3360,
        titular_local_exercicio="EMEF TESTE 1",
    )
    return ato


@pytest.fixture
def designacao_2(db):
    """Método designacao 2."""
    ato = AtoAdministrativo.objects.create(
        tipo="DESIGNACAO",
        numero_portaria="002/2024",
        ano_vigente="2024",
        sei_numero="6018.2024/0002345-6",
        doc=None,
        ativo=True,
        status_publicacao=AtoAdministrativo.StatusPublicacao.NAO_PUBLICADO,
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
def designacao_3(db):
    """Método designacao 3."""
    ato = AtoAdministrativo.objects.create(
        tipo="DESIGNACAO",
        numero_portaria="003/2024",
        ano_vigente="2024",
        sei_numero="6018.2024/0003456-7",
        doc=None,
        ativo=True,
        status_publicacao=AtoAdministrativo.StatusPublicacao.NAO_PUBLICADO,
    )
    DesignacaoDetalhe.objects.create(
        ato=ato,
        dre_nome="DRE IPIRANGA",
        unidade_proponente="EMEF TESTE 2",
        codigo_hierarquico="108700",
        indicado_nome_servidor="CARLOS SILVA",
        indicado_nome_civil="Carlos da Silva",
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
        numero_portaria="003/2024",
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
        numero_portaria="004/2024",
        ano_vigente="2024",
        sei_numero="6018.2024/0004567-8",
        doc=None,
        ativo=True,
        ato_pai=designacao_1,
    )


@pytest.fixture
def insubsistencia_cessacao(db, cessacao):
    """Método insubsistencia cessação."""
    return AtoAdministrativo.objects.create(
        tipo="INSUBSISTENCIA",
        numero_portaria="005/2024",
        ano_vigente="2024",
        sei_numero="6018.2024/0004567-8",
        doc=None,
        ativo=True,
        ato_pai=cessacao,
    )


@pytest.fixture
def apostila(db, designacao_1):
    """Método apostila com observação."""
    ato = AtoAdministrativo.objects.create(
        tipo="APOSTILA",
        numero_portaria="",
        ano_vigente="",
        sei_numero="6018.2024/0005678-9",
        doc=None,
        ativo=True,
        ato_pai=designacao_1,
    )
    ApostilaDetalhe.objects.create(
        ato=ato, observacao="Retificacao de dados funcionais"
    )
    return ato


@pytest.fixture
def insubsistencia_com_observacao(db, designacao_1):
    """Método insubsistencia com observação."""
    ato = AtoAdministrativo.objects.create(
        tipo="INSUBSISTENCIA",
        numero_portaria="006/2024",
        ano_vigente="2024",
        sei_numero="6018.2024/0006789-0",
        doc=None,
        ativo=True,
        ato_pai=designacao_1,
    )
    InsubsistenciaDetalhe.objects.create(
        ato=ato, observacoes="Ato sem efeito por divergencia documental"
    )
    return ato


# ─── Testes ───────────────────────────────────────────────────────────────────


@pytest.mark.django_db
class TestAtoAdministrativoFilter:

    # tipo
    """Testes para atos administrativos filter."""

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

    def test_filtro_tipo_designacao_e_cessacao(
        self, designacao_1, designacao_2, cessacao, insubsistencia
    ):
        """Verifica filtro combinado de designação e cessação."""
        qs = apply_filter({"tipo": "DESIGNACAO_CESSACAO"})
        assert qs.count() == 3
        assert all(a.tipo in ("DESIGNACAO", "CESSACAO") for a in qs)

    def test_filtro_tipo_insubsistencia(
        self, designacao_1, cessacao, insubsistencia
    ):
        """Verifica filtro tipo insubsistencia."""
        qs = apply_filter({"tipo": "INSUBSISTENCIA"})
        assert qs.count() == 1
        assert qs.first() == insubsistencia

    def test_filtro_tipo_insubsistencia_designacao(
        self, designacao_1, cessacao, insubsistencia
    ):
        """Verifica filtro tipo insubsistencia."""
        qs = apply_filter({"tipo": "INSUBSISTENCIA_DESIGNACAO"})
        assert qs.count() == 1
        assert qs.first() == insubsistencia

    def test_filtro_tipo_insubsistencia_cessacao(
        self, cessacao, insubsistencia_cessacao
    ):
        """Verifica filtro tipo insubsistencia cessação."""
        qs = apply_filter({"tipo": "INSUBSISTENCIA_CESSACAO"})
        assert qs.count() == 1
        assert qs.first() == insubsistencia_cessacao

    def test_filtro_portaria(self, designacao_1, designacao_2):
        # Filtra apenas designação no queryset
        """Verifica filtro portaria."""
        qs = AtoAdministrativo.objects.all()
        f = AtoAdministrativoFilter(data={"portaria": "001/2024"}, queryset=qs)
        assert f.qs.count() == 1
        assert f.qs.first().numero_portaria == "001/2024"

    def test_filtro_rf(self, designacao_1, designacao_2, designacao_3):
        # Filtra apenas designação no queryset
        """Verifica filtro rf titulares ou indicados."""
        qs = AtoAdministrativo.objects.all()
        f = AtoAdministrativoFilter(data={"rf": "87654321"}, queryset=qs)
        assert f.qs.count() == 2
        assert f.qs.first().designacao_detalhe.indicado_rf == "87654321"

    def test_filtro_nome_titular_e_indicado(
        self, designacao_1, designacao_2, designacao_3
    ):
        # Filtra apenas cessação no queryset
        """Verifica filtro se existe nome Joao no titular ou indicado."""
        qs = AtoAdministrativo.objects.select_related("designacao_detalhe")
        f = AtoAdministrativoFilter(
            data={"nome_titular_e_indicado": "Joao"}, queryset=qs
        )
        assert f.qs.count() == 2
        for x in f.qs:
            assert any(
                "Joao" in nome
                for nome in [
                    x.designacao_detalhe.titular_nome_servidor,
                    x.designacao_detalhe.titular_nome_civil,
                    x.designacao_detalhe.indicado_nome_servidor,
                    x.designacao_detalhe.indicado_nome_civil,
                ]
            )

    def test_filtro_status_nao_publicacao(self, designacao_1, designacao_2):
        # Filtra apenas atos não publicados no queryset
        """Verifica filtro status_publicacao."""
        qs = AtoAdministrativo.objects.all()
        f = AtoAdministrativoFilter(
            data={"status_publicacao": "NAO_PUBLICADO"}, queryset=qs
        )
        assert f.qs.count() == 2
        for x in f.qs:
            assert x.status_publicacao == "NAO_PUBLICADO"

    def test_filtro_status_publicado(self, designacao_1, designacao_2):
        # Filtra apenas atos publicados no queryset
        """Verifica filtro status_publicacao."""
        qs = AtoAdministrativo.objects.all()
        f = AtoAdministrativoFilter(
            data={"status_publicacao": "PUBLICADO"}, queryset=qs
        )
        assert f.qs.count() == 0

    def test_filtro_numero_sei(self, designacao_1, designacao_2):
        # Filtra apenas designação no queryset
        """Verifica filtro numero_sei."""
        qs = AtoAdministrativo.objects.all()
        f = AtoAdministrativoFilter(
            data={"numero_sei": "6018.2024/0001234-5"}, queryset=qs
        )
        assert f.qs.count() == 1
        assert f.qs.first().sei_numero == "6018.2024/0001234-5"

    def test_filtro_periodo_com_dados(self, designacao_1, designacao_2):
        # Filtra apenas designação no queryset
        """Verifica filtro periodo com dados."""
        qs = AtoAdministrativo.objects.all()
        after = datetime.datetime.now() - datetime.timedelta(days=1)
        before = datetime.datetime.now() + datetime.timedelta(days=1)
        f = AtoAdministrativoFilter(
            data={"periodo_after": after, "periodo_before": before},
            queryset=qs,
        )
        assert f.qs.count() == 2

    def test_filtro_periodo_sem_dados(self, designacao_1, designacao_2):
        # Filtra apenas designação no queryset
        """Verifica filtro periodo sem dados."""
        qs = AtoAdministrativo.objects.all()
        after = "2024-01-01"
        before = "2024-12-31"
        f = AtoAdministrativoFilter(
            data={"periodo_after": after, "periodo_before": before},
            queryset=qs,
        )
        assert f.qs.count() == 0

    def test_filtro_ato_id_por_ato_pai(
        self, designacao_1, cessacao, insubsistencia_cessacao
    ):
        """Verifica filtro ato_id por relacionamento de ato pai."""
        qs = apply_filter({"ato_id": cessacao.id})
        assert qs.count() == 2
        assert qs.first() == cessacao

    def test_filtro_ato_id_por_ato_raiz(
        self, designacao_1, cessacao, insubsistencia_cessacao
    ):
        """Verifica filtro ato_id por relacionamento de ato raiz."""
        qs = apply_filter({"ato_id": designacao_1.id})
        assert cessacao in qs
        assert insubsistencia_cessacao in qs

    def test_filtro_observacao_apostila(
        self, designacao_1, apostila, insubsistencia_com_observacao
    ):
        """Verifica filtro observacao em apostila detalhe."""
        qs = apply_filter({"observacao": "retificacao"})
        assert qs.count() == 1
        assert qs.first() == apostila

    def test_filtro_observacao_insubsistencia(
        self, designacao_1, apostila, insubsistencia_com_observacao
    ):
        """Verifica filtro observacao em insubsistencia detalhe."""
        qs = apply_filter({"observacao": "divergencia documental"})
        assert qs.count() == 1
        assert qs.first() == insubsistencia_com_observacao
