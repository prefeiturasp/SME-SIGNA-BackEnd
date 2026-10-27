"""Testes para o model CargoBase."""

from datetime import date

import pytest
from django.db import IntegrityError

from apps.gestao.__tests__.factories import criar_cargo_base
from apps.gestao.models.cargo_base import CargoBase


@pytest.mark.django_db
def test_str_retorna_codigo_e_descricao_resumida():
    """Verifica a representação textual do cargo base."""
    cargo = criar_cargo_base(
        codigo_cargo="9379", descricao_resumida="Coordenador Pedagógico"
    )

    assert str(cargo) == "9379 - Coordenador Pedagógico"


@pytest.mark.django_db
def test_status_default_e_ativo():
    """Verifica que o status padrão de um cargo base é ATIVO."""
    cargo = CargoBase.objects.create(
        codigo_cargo="9182",
        descricao_completa="SECRETARIO DE ESCOLA",
        descricao_resumida="Secretário de Escola",
        grupamento=CargoBase.Grupamento.APOIO_EDUCACAO,
        situacao_funcional=CargoBase.SituacaoFuncional.COMISSIONADO,
    )

    assert cargo.status == CargoBase.Status.ATIVO


@pytest.mark.django_db
def test_defaults_utilizacao_do_cargo():
    """Verifica os defaults dos campos de utilização do cargo."""
    cargo = CargoBase.objects.create(
        codigo_cargo="9183",
        descricao_completa="PROFESSOR",
        descricao_resumida="Professor",
        grupamento=CargoBase.Grupamento.DOCENTES,
        situacao_funcional=CargoBase.SituacaoFuncional.EFETIVO,
    )

    assert cargo.utilizado_para_funcoes is True
    assert cargo.utilizado_para_designacoes is True
    assert cargo.utilizado_para_ste is True
    assert cargo.utilizado_para_permutas is False
    assert cargo.cargo_base_ficticio is False
    assert cargo.testar_laudo is False
    assert cargo.pesquisar_licencas_no_sigpec is False
    assert cargo.permite_substituicao is False
    assert cargo.possui_periodo_fechado is False


@pytest.mark.django_db
def test_quantidade_maxima_de_dias_de_licenca_default_e_zero():
    """Verifica que a quantidade máxima de dias de licença padrão é zero."""
    cargo = CargoBase.objects.create(
        codigo_cargo="9184",
        descricao_completa="AUXILIAR DE SALA",
        descricao_resumida="Auxiliar de Sala",
        grupamento=CargoBase.Grupamento.APOIO_EDUCACAO,
        situacao_funcional=CargoBase.SituacaoFuncional.CONTRATADO,
    )

    assert cargo.quantidade_maxima_de_dias_de_licenca == 0


@pytest.mark.django_db
def test_quantidade_maxima_de_dias_de_licenca_aceita_null():
    """Verifica que a quantidade máxima de dias de licença aceita null."""
    cargo = criar_cargo_base(
        codigo_cargo="9185",
        quantidade_maxima_de_dias_de_licenca=None,
    )

    cargo.refresh_from_db()
    assert cargo.quantidade_maxima_de_dias_de_licenca is None


@pytest.mark.django_db
def test_data_fim_periodo_persiste_valor():
    """Verifica que data_fim_periodo é persistida corretamente."""
    cargo = criar_cargo_base(
        codigo_cargo="9186",
        possui_periodo_fechado=True,
        data_fim_periodo=date(2026, 12, 31),
    )

    cargo.refresh_from_db()
    assert cargo.possui_periodo_fechado is True
    assert cargo.data_fim_periodo == date(2026, 12, 31)


@pytest.mark.django_db
def test_data_fim_periodo_default_e_null():
    """Verifica que data_fim_periodo é null por padrão."""
    cargo = criar_cargo_base(codigo_cargo="9187")

    assert cargo.data_fim_periodo is None


@pytest.mark.django_db
def test_criado_em_e_preenchido_automaticamente():
    """Verifica que criado_em é preenchido na criação."""
    cargo = criar_cargo_base(codigo_cargo="9188")

    assert cargo.criado_em is not None


@pytest.mark.django_db
def test_ordering_padrao_e_por_descricao_resumida():
    """Verifica que a listagem padrão ordena por descricao_resumida."""
    cargo_beta = criar_cargo_base(
        codigo_cargo="9001", descricao_resumida="Beta"
    )
    cargo_alpha = criar_cargo_base(
        codigo_cargo="9002", descricao_resumida="Alpha"
    )

    resultado = list(
        CargoBase.objects.filter(codigo_cargo__in=["9001", "9002"])
    )

    assert resultado == [cargo_alpha, cargo_beta]


@pytest.mark.django_db
def test_meta_db_table():
    """Verifica o nome da tabela no banco de dados."""
    assert CargoBase._meta.db_table == "cargo_base"


@pytest.mark.django_db
def test_codigo_cargo_deve_ser_unico():
    """Verifica que não é possível cadastrar dois cargos com o mesmo código."""
    criar_cargo_base(codigo_cargo="9085")

    with pytest.raises(IntegrityError):
        criar_cargo_base(codigo_cargo="9085")
