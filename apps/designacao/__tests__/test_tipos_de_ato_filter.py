"""Testes das opções e da decomposição do parâmetro ``tipo`` de atos.

As opções são compartilhadas pelas listagens de portarias, de atos
administrativos e pelo histórico de designações.
"""

import pytest

from apps.designacao.api.filters.tipos_de_ato import (
    TIPO_CHOICES,
    TIPO_CHOICES_SIMPLES,
    dividir_tipo_composto,
)
from apps.designacao.models.ato_administrativo import AtoAdministrativo


def test_tipo_choices_inclui_os_tipos_do_modelo():
    """Toda opção gravada em `AtoAdministrativo.tipo` é aceita no filtro."""
    valores = [valor for valor, _rotulo in TIPO_CHOICES]

    assert set(AtoAdministrativo.Tipo.values) <= set(valores)


def test_tipo_choices_inclui_a_uniao_e_os_compostos():
    """As opções trazem `DESIGNACAO_CESSACAO` e os pares tipo/pai."""
    valores = [valor for valor, _rotulo in TIPO_CHOICES]

    assert "DESIGNACAO_CESSACAO" in valores
    assert "APOSTILA_CESSACAO" in valores
    assert "INSUBSISTENCIA_INSUBSISTENCIA" in valores


def test_tipo_choices_simples_nao_traz_compostos():
    """A listagem de portarias não aceita `TIPO_TIPO_PAI`."""
    valores = [valor for valor, _rotulo in TIPO_CHOICES_SIMPLES]

    assert "DESIGNACAO_CESSACAO" in valores
    assert [
        valor
        for valor in valores
        if "_" in valor and valor != "DESIGNACAO_CESSACAO"
    ] == []


def test_todo_pseudo_tipo_composto_respeita_a_hierarquia():
    """Cada `TIPO_TIPO_PAI` combina tipos que a regra de negócio permite."""
    for valor, _rotulo in TIPO_CHOICES:
        # `DESIGNACAO_CESSACAO` é uma união, não um par tipo/pai.
        if valor == "DESIGNACAO_CESSACAO":
            continue
        composto = dividir_tipo_composto(valor)
        if composto is None:
            continue
        tipo, pai = composto
        assert pai in AtoAdministrativo.TIPOS_PAI_VALIDOS[tipo]


@pytest.mark.parametrize(
    ("valor", "esperado"),
    [
        ("APOSTILA_CESSACAO", ("APOSTILA", "CESSACAO")),
        (
            "INSUBSISTENCIA_INSUBSISTENCIA",
            ("INSUBSISTENCIA", "INSUBSISTENCIA"),
        ),
        # Só o primeiro separador divide o valor.
        ("A_B_C", ("A", "B_C")),
        ("APOSTILA", None),
        ("DESIGNACAO", None),
    ],
)
def test_dividir_tipo_composto(valor, esperado):
    """Decompõe o pseudo-tipo em (tipo, tipo do pai)."""
    assert dividir_tipo_composto(valor) == esperado
