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


@pytest.mark.django_db
def test_resolver_ativo_retorna_modelo_ativo_da_combinacao_informada():
    """Verifica que resolver_ativo encontra o modelo ativo pelo tipo."""
    esperado = criar_modelo_portaria(
        tipo_portaria=AtoAdministrativo.Tipo.APOSTILA,
        tipo_ato_pai=AtoAdministrativo.Tipo.DESIGNACAO,
    )

    resultado = ModeloPortariaService.resolver_ativo(
        AtoAdministrativo.Tipo.APOSTILA,
        AtoAdministrativo.Tipo.DESIGNACAO,
        ModeloPortaria.TipoCargo.CARGO_VAGO,
    )

    assert resultado == esperado


@pytest.mark.django_db
def test_resolver_ativo_distingue_por_tipo_cargo():
    """Verifica que cargo vago e cargo disponível resolvem modelos distintos."""
    vago = criar_modelo_portaria(
        tipo_portaria=AtoAdministrativo.Tipo.DESIGNACAO,
        tipo_cargo=ModeloPortaria.TipoCargo.CARGO_VAGO,
        nome_modelo="Designação cargo vago",
    )
    disponivel = criar_modelo_portaria(
        tipo_portaria=AtoAdministrativo.Tipo.DESIGNACAO,
        tipo_cargo=ModeloPortaria.TipoCargo.CARGO_DISPONIVEL,
        nome_modelo="Designação cargo disponível",
    )

    resultado_vago = ModeloPortariaService.resolver_ativo(
        AtoAdministrativo.Tipo.DESIGNACAO,
        tipo_cargo=ModeloPortaria.TipoCargo.CARGO_VAGO,
    )
    resultado_disponivel = ModeloPortariaService.resolver_ativo(
        AtoAdministrativo.Tipo.DESIGNACAO,
        tipo_cargo=ModeloPortaria.TipoCargo.CARGO_DISPONIVEL,
    )

    assert resultado_vago == vago
    assert resultado_disponivel == disponivel


@pytest.mark.django_db
def test_resolver_ativo_ignora_modelo_inativo():
    """Verifica que resolver_ativo não retorna modelo com status inativo."""
    criar_modelo_portaria(
        tipo_portaria=AtoAdministrativo.Tipo.DESIGNACAO,
        status=ModeloPortaria.Status.INATIVO,
    )

    resultado = ModeloPortariaService.resolver_ativo(
        AtoAdministrativo.Tipo.DESIGNACAO,
        tipo_cargo=ModeloPortaria.TipoCargo.CARGO_VAGO,
    )

    assert resultado is None


@pytest.mark.django_db
def test_resolver_ativo_retorna_none_quando_nao_ha_modelo():
    """Verifica que resolver_ativo retorna None sem modelo cadastrado."""
    resultado = ModeloPortariaService.resolver_ativo(
        AtoAdministrativo.Tipo.CESSACAO
    )

    assert resultado is None


@pytest.mark.django_db
def test_resolver_ativo_retorna_o_mais_recente_quando_ha_mais_de_um():
    """Verifica que, sem constraint de unicidade, prevalece o mais recente.

    Hoje não há garantia de um único modelo ativo por combinação de
    tipos — enquanto essa regra não existir, o mais recente é usado.
    """
    criar_modelo_portaria(
        tipo_portaria=AtoAdministrativo.Tipo.DESIGNACAO,
        nome_modelo="Modelo antigo",
    )
    mais_recente = criar_modelo_portaria(
        tipo_portaria=AtoAdministrativo.Tipo.DESIGNACAO,
        nome_modelo="Modelo recente",
    )

    resultado = ModeloPortariaService.resolver_ativo(
        AtoAdministrativo.Tipo.DESIGNACAO,
        tipo_cargo=ModeloPortaria.TipoCargo.CARGO_VAGO,
    )

    assert resultado == mais_recente
