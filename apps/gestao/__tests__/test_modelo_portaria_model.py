"""Testes para o model ModeloPortaria."""

from datetime import timedelta

import pytest
from django.utils import timezone

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


@pytest.mark.django_db
def test_tipo_ato_pai_default_e_vazio():
    """Verifica que tipo_ato_pai é string vazia por padrão."""
    modelo = criar_modelo_portaria()

    assert modelo.tipo_ato_pai == ""


@pytest.mark.django_db
def test_tipo_ato_pai_persiste_valor():
    """Verifica que tipo_ato_pai é persistido para apostila/insubsistência."""
    modelo = criar_modelo_portaria(
        nome_modelo="Apostila de cessação",
        tipo_portaria=AtoAdministrativo.Tipo.APOSTILA,
        tipo_ato_pai=AtoAdministrativo.Tipo.CESSACAO,
    )

    modelo.refresh_from_db()
    assert modelo.tipo_ato_pai == AtoAdministrativo.Tipo.CESSACAO


@pytest.mark.django_db
def test_ordering_padrao_e_por_criado_em_decrescente():
    """Verifica que a listagem padrão traz os modelos mais recentes primeiro."""
    mais_antigo = criar_modelo_portaria(nome_modelo="Modelo A")
    mais_novo = criar_modelo_portaria(nome_modelo="Modelo B")

    agora = timezone.now()
    ModeloPortaria.objects.filter(pk=mais_antigo.pk).update(
        criado_em=agora - timedelta(days=1)
    )
    ModeloPortaria.objects.filter(pk=mais_novo.pk).update(criado_em=agora)

    resultado = list(ModeloPortaria.objects.all())

    assert resultado == [mais_novo, mais_antigo]


def test_variaveis_disponiveis_sem_tipo_cargo_devolve_todas():
    """Sem tipo de cargo, nenhuma variável é omitida."""
    assert ModeloPortaria.variaveis_disponiveis() == list(
        ModeloPortaria.Variavel.choices
    )


def test_variaveis_disponiveis_com_cargo_vago_inclui_titular():
    """Cargo vago mantém a lista completa."""
    valores = dict(
        ModeloPortaria.variaveis_disponiveis(
            ModeloPortaria.TipoCargo.CARGO_VAGO
        )
    )

    assert ModeloPortaria.Variavel.TITULAR in valores


def test_variaveis_disponiveis_com_cargo_disponivel_omite_titular():
    """Cargo disponível omite apenas TITULAR."""
    valores = [
        valor
        for valor, _rotulo in ModeloPortaria.variaveis_disponiveis(
            ModeloPortaria.TipoCargo.CARGO_DISPONIVEL
        )
    ]

    assert ModeloPortaria.Variavel.TITULAR not in valores
    assert len(valores) == len(ModeloPortaria.Variavel.choices) - 1


def test_variaveis_invalidas_para_tipo_cargo():
    """Aponta só as variáveis que não valem para o tipo de cargo."""
    variaveis = [
        ModeloPortaria.Variavel.TITULAR,
        ModeloPortaria.Variavel.NOME_SERVIDOR,
    ]

    assert ModeloPortaria.variaveis_invalidas_para_tipo_cargo(
        variaveis, ModeloPortaria.TipoCargo.CARGO_DISPONIVEL
    ) == [ModeloPortaria.Variavel.TITULAR]
    assert (
        ModeloPortaria.variaveis_invalidas_para_tipo_cargo(
            variaveis, ModeloPortaria.TipoCargo.CARGO_VAGO
        )
        == []
    )
