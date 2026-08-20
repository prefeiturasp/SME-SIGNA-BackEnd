"""Testes para o ModeloPortariaService."""

import pytest

from apps.designacao.models.ato_administrativo import AtoAdministrativo
from apps.gestao.__tests__.factories import criar_modelo_portaria
from apps.gestao.models.modelo_portaria import ModeloPortaria
from apps.gestao.services.modelo_portaria_service import ModeloPortariaService


@pytest.mark.django_db
def test_listar_retorna_todos_os_modelos_cadastrados():
    """Verifica que listar retorna todos os modelos de portaria cadastrados."""
    criar_modelo_portaria(nome_modelo="Modelo 1")
    criar_modelo_portaria(nome_modelo="Modelo 2")

    resultado = ModeloPortariaService.listar()

    assert resultado.count() == 2


@pytest.mark.django_db
def test_criar_cria_modelo_portaria_com_os_dados_informados():
    """Verifica que criar persiste um modelo de portaria com os dados informados."""
    dados = {
        "tipo_portaria": AtoAdministrativo.Tipo.DESIGNACAO,
        "nome_modelo": "Designação diretor de escola",
        "tipo_cargo": ModeloPortaria.TipoCargo.CARGO_VAGO,
        "variaveis": [ModeloPortaria.Variavel.NOME_SERVIDOR],
        "texto_portaria": "Texto qualquer",
    }

    modelo = ModeloPortariaService.criar(dados)

    assert modelo.pk is not None
    assert ModeloPortaria.objects.filter(
        nome_modelo="Designação diretor de escola"
    ).exists()
