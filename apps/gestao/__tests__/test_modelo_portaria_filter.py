"""Testes para o ModeloPortariaFilter."""

import datetime

import pytest
from django.utils import timezone

from apps.designacao.models.ato_administrativo import AtoAdministrativo
from apps.gestao.__tests__.factories import criar_modelo_portaria
from apps.gestao.api.filters.modelo_portaria_filter import ModeloPortariaFilter
from apps.gestao.models.modelo_portaria import ModeloPortaria


@pytest.mark.django_db
def test_filtra_por_nome_modelo_parcial():
    """Verifica que o filtro por nome do modelo faz busca parcial."""
    criar_modelo_portaria(nome_modelo="Designação diretor de escola")
    criar_modelo_portaria(nome_modelo="Cessação diretor de escola")

    resultado = ModeloPortariaFilter(
        {"nome_modelo": "designação"},
        queryset=ModeloPortaria.objects.all(),
    ).qs

    assert resultado.count() == 1
    assert resultado.first().nome_modelo == "Designação diretor de escola"


@pytest.mark.django_db
def test_filtra_por_tipo_portaria():
    """Verifica que o filtro por tipo de portaria retorna os compatíveis."""
    criar_modelo_portaria(
        nome_modelo="Designação diretor de escola",
        tipo_portaria=AtoAdministrativo.Tipo.DESIGNACAO,
    )
    criar_modelo_portaria(
        nome_modelo="Cessação diretor de escola",
        tipo_portaria=AtoAdministrativo.Tipo.CESSACAO,
    )

    resultado = ModeloPortariaFilter(
        {"tipo_portaria": AtoAdministrativo.Tipo.CESSACAO},
        queryset=ModeloPortaria.objects.all(),
    ).qs

    assert resultado.count() == 1
    assert resultado.first().nome_modelo == "Cessação diretor de escola"


@pytest.mark.django_db
def test_filtra_por_tipo_ato_pai():
    """Verifica que o filtro por tipo_ato_pai distingue apostilas."""
    criar_modelo_portaria(
        nome_modelo="Apostila de designação",
        tipo_portaria=AtoAdministrativo.Tipo.APOSTILA,
        tipo_ato_pai=AtoAdministrativo.Tipo.DESIGNACAO,
    )
    criar_modelo_portaria(
        nome_modelo="Apostila de cessação",
        tipo_portaria=AtoAdministrativo.Tipo.APOSTILA,
        tipo_ato_pai=AtoAdministrativo.Tipo.CESSACAO,
    )

    resultado = ModeloPortariaFilter(
        {
            "tipo_portaria": AtoAdministrativo.Tipo.APOSTILA,
            "tipo_ato_pai": AtoAdministrativo.Tipo.CESSACAO,
        },
        queryset=ModeloPortaria.objects.all(),
    ).qs

    assert resultado.count() == 1
    assert resultado.first().nome_modelo == "Apostila de cessação"


@pytest.mark.django_db
def test_filtra_por_status():
    """Verifica que o filtro por status retorna os compatíveis."""
    criar_modelo_portaria(
        nome_modelo="Modelo ativo", status=ModeloPortaria.Status.ATIVO
    )
    criar_modelo_portaria(
        nome_modelo="Modelo inativo", status=ModeloPortaria.Status.INATIVO
    )

    resultado = ModeloPortariaFilter(
        {"status": ModeloPortaria.Status.INATIVO},
        queryset=ModeloPortaria.objects.all(),
    ).qs

    assert resultado.count() == 1
    assert resultado.first().nome_modelo == "Modelo inativo"


@pytest.mark.django_db
def test_filtra_por_tipo_cargo():
    """Verifica que o filtro por tipo de cargo retorna os compatíveis."""
    criar_modelo_portaria(
        nome_modelo="Modelo cargo vago",
        tipo_cargo=ModeloPortaria.TipoCargo.CARGO_VAGO,
    )
    criar_modelo_portaria(
        nome_modelo="Modelo cargo disponível",
        tipo_cargo=ModeloPortaria.TipoCargo.CARGO_DISPONIVEL,
    )

    resultado = ModeloPortariaFilter(
        {"tipo_cargo": ModeloPortaria.TipoCargo.CARGO_DISPONIVEL},
        queryset=ModeloPortaria.objects.all(),
    ).qs

    assert resultado.count() == 1
    assert resultado.first().nome_modelo == "Modelo cargo disponível"


@pytest.mark.django_db
def test_combina_multiplos_filtros():
    """Verifica que múltiplos filtros preenchidos são combinados (E lógico)."""
    criar_modelo_portaria(
        nome_modelo="Designação diretor de escola",
        tipo_portaria=AtoAdministrativo.Tipo.DESIGNACAO,
        status=ModeloPortaria.Status.ATIVO,
    )
    criar_modelo_portaria(
        nome_modelo="Designação coordenador",
        tipo_portaria=AtoAdministrativo.Tipo.DESIGNACAO,
        status=ModeloPortaria.Status.INATIVO,
    )

    resultado = ModeloPortariaFilter(
        {
            "tipo_portaria": AtoAdministrativo.Tipo.DESIGNACAO,
            "status": ModeloPortaria.Status.ATIVO,
        },
        queryset=ModeloPortaria.objects.all(),
    ).qs

    assert resultado.count() == 1
    assert resultado.first().nome_modelo == "Designação diretor de escola"


@pytest.mark.django_db
def test_filtra_por_criado_em_intervalo():
    """Verifica que o filtro por criado_em retorna os no intervalo."""
    antigo = criar_modelo_portaria(nome_modelo="Modelo antigo")
    recente = criar_modelo_portaria(nome_modelo="Modelo recente")

    ModeloPortaria.objects.filter(id=antigo.id).update(
        criado_em=timezone.make_aware(datetime.datetime(2026, 1, 1))
    )
    ModeloPortaria.objects.filter(id=recente.id).update(
        criado_em=timezone.make_aware(datetime.datetime(2026, 6, 1))
    )

    resultado = ModeloPortariaFilter(
        {
            "criado_em_after": "2026-05-01",
            "criado_em_before": "2026-07-01",
        },
        queryset=ModeloPortaria.objects.all(),
    ).qs

    assert resultado.count() == 1
    assert resultado.first().nome_modelo == "Modelo recente"


@pytest.mark.django_db
def test_sem_filtros_retorna_todos():
    """Verifica que a ausência de filtros retorna todos os modelos."""
    criar_modelo_portaria(nome_modelo="Modelo 1")
    criar_modelo_portaria(nome_modelo="Modelo 2")

    resultado = ModeloPortariaFilter(
        {}, queryset=ModeloPortaria.objects.all()
    ).qs

    assert resultado.count() == 2
