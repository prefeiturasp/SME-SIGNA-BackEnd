"""Testes para o RegraPortariaService."""

import pytest

from apps.gestao.__tests__.factories import criar_regra_portaria
from apps.gestao.models.regra_portaria import RegraPortaria
from apps.gestao.services.regra_portaria_service import RegraPortariaService


@pytest.mark.django_db
def test_listar_retorna_todas_as_regras_cadastradas():
    """Verifica que listar retorna todas as regras de portaria cadastradas."""
    criar_regra_portaria(codigo_cargo_eol="3360")
    criar_regra_portaria(codigo_cargo_eol="3182")

    resultado = RegraPortariaService.listar()

    assert resultado.count() == 2


@pytest.mark.django_db
def test_criar_cria_regra_portaria_com_os_dados_informados():
    """Verifica que criar persiste uma regra de portaria informada."""
    dados = {
        "descricao_resumida_cargo": "Diretor",
        "descricao_completa_cargo": "Diretor de escola",
        "codigo_cargo_eol": "3360",
        "tipo_modulo": RegraPortaria.TipoModulo.TURMAS,
        "texto_publicacao": "Texto qualquer",
        "emitente": RegraPortaria.Emitente.SECRETARIO_MUNICIPAL_EDUCACAO,
    }

    regra = RegraPortariaService.criar(dados)

    assert regra.pk is not None
    assert RegraPortaria.objects.filter(codigo_cargo_eol="3360").exists()


@pytest.mark.django_db
def test_atualizar_altera_os_campos_informados():
    """Verifica que atualizar altera os campos informados e persiste."""
    regra = criar_regra_portaria(
        descricao_resumida_cargo="Diretor",
        status=RegraPortaria.Status.ATIVO,
    )

    regra_atualizada = RegraPortariaService.atualizar(
        regra,
        {
            "descricao_resumida_cargo": "Diretor de Escola Municipal",
            "status": RegraPortaria.Status.INATIVO,
        },
    )

    regra_atualizada.refresh_from_db()
    assert regra_atualizada.descricao_resumida_cargo == (
        "Diretor de Escola Municipal"
    )
    assert regra_atualizada.status == RegraPortaria.Status.INATIVO
