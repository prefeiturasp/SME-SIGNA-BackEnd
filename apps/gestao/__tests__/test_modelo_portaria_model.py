"""Testes para o model ModeloPortaria."""

import pytest

from apps.designacao.models.ato_administrativo import AtoAdministrativo
from apps.gestao.__tests__.factories import criar_modelo_portaria
from apps.gestao.models.modelo_portaria import ModeloPortaria


@pytest.mark.django_db
def test_str_retorna_nome_do_modelo():
    """Verifica a representação textual do modelo de portaria."""
    modelo = criar_modelo_portaria(nome_modelo="Designação diretor de escola")

    assert str(modelo) == "Designação diretor de escola"


@pytest.mark.django_db
def test_status_default_e_ativo():
    """Verifica que o status padrão de um modelo de portaria é ATIVO."""
    modelo = ModeloPortaria.objects.create(
        tipo_portaria=AtoAdministrativo.Tipo.DESIGNACAO,
        nome_modelo="Designação diretor de escola",
        tipo_cargo=ModeloPortaria.TipoCargo.CARGO_VAGO,
        texto_portaria="Texto qualquer",
    )

    assert modelo.status == ModeloPortaria.Status.ATIVO


@pytest.mark.django_db
def test_variaveis_default_e_lista_vazia():
    """Verifica que o campo variaveis é uma lista vazia por padrão."""
    modelo = ModeloPortaria.objects.create(
        tipo_portaria=AtoAdministrativo.Tipo.DESIGNACAO,
        nome_modelo="Designação diretor de escola",
        tipo_cargo=ModeloPortaria.TipoCargo.CARGO_VAGO,
        texto_portaria="Texto qualquer",
    )

    assert modelo.variaveis == []


@pytest.mark.django_db
def test_variaveis_persiste_lista_de_chaves():
    """Verifica que as variáveis selecionadas são persistidas corretamente."""
    modelo = criar_modelo_portaria(
        variaveis=[
            ModeloPortaria.Variavel.NOME_SERVIDOR,
            ModeloPortaria.Variavel.NUMERO_RF,
            ModeloPortaria.Variavel.UNIDADE,
        ]
    )

    modelo.refresh_from_db()
    assert modelo.variaveis == ["NOME_SERVIDOR", "NUMERO_RF", "UNIDADE"]
