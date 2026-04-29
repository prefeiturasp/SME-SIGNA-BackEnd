import pytest
from django.core.exceptions import ValidationError

from apps.designacao.models.designacao import Designacao
from apps.designacao.models.cessacao import Cessacao
from apps.designacao.models.apostila import Apostila


def criar_designacao():
    return Designacao.objects.create(
        dre_nome="DRE",
        unidade_proponente="Unidade",
        codigo_hierarquico="123",
        indicado_nome_civil="Nome",
        indicado_nome_servidor="Nome",
        indicado_rf="1234567",
        indicado_vinculo=1,
        indicado_cargo_base="Cargo",
        indicado_lotacao="Lotacao",
        indicado_local_exercicio="Local",
        numero_portaria="123",
        ano_vigente="2024",
        sei_numero="123",
        data_inicio="2024-01-01",
        tipo_vaga=Designacao.TipoVaga.VAGO,
    )


def criar_cessacao(designacao):
    return Cessacao.objects.create(
        designacao=designacao,
        numero_portaria="12345",
        ano_vigente="2024",
        sei_numero="999999",
        a_pedido=True,
        data_designacao="2024-03-10"
    )


# 🟢 TESTE 1 — criação válida
@pytest.mark.django_db
def test_apostila_valida():
    designacao = criar_designacao()

    apostila = Apostila(
        tipo=Apostila.Tipo.APOSTILA,
        designacao=designacao,
        sei_numero="123456",
        observacao="Correção"
    )

    apostila.full_clean()
    apostila.save()

    assert apostila.id is not None


@pytest.mark.django_db
def test_apostila_deve_ter_um_unico_vinculo():
    designacao = criar_designacao()
    cessacao = criar_cessacao(designacao)

    apostila = Apostila(
        tipo=Apostila.Tipo.APOSTILA,
        designacao=designacao,
        cessacao=cessacao,
        sei_numero="123456",
        observacao="Teste"
    )

    with pytest.raises(ValidationError):
        apostila.full_clean()


@pytest.mark.django_db
def test_anulacao_sem_referencia_falha():
    designacao = criar_designacao()

    apostila = Apostila(
        tipo=Apostila.Tipo.ANULACAO,
        designacao=designacao,
        sei_numero="123456",
        observacao="Teste"
    )

    with pytest.raises(ValidationError):
        apostila.full_clean()


@pytest.mark.django_db
def test_anulacao_valida():
    designacao = criar_designacao()

    original = Apostila.objects.create(
        tipo=Apostila.Tipo.APOSTILA,
        designacao=designacao,
        sei_numero="111",
        observacao="Original"
    )

    anulacao = Apostila(
        tipo=Apostila.Tipo.ANULACAO,
        designacao=designacao,
        apostila_referencia=original,
        sei_numero="222",
        observacao="Anulação"
    )

    anulacao.full_clean()
    anulacao.save()

    assert original.anulacoes.count() == 1


@pytest.mark.django_db
def test_apostila_nao_pode_ter_referencia():
    designacao = criar_designacao()

    referencia = Apostila.objects.create(
        tipo=Apostila.Tipo.APOSTILA,
        designacao=designacao,
        sei_numero="111",
        observacao="Original"
    )

    apostila = Apostila(
        tipo=Apostila.Tipo.APOSTILA,
        designacao=designacao,
        apostila_referencia=referencia,
        sei_numero="222",
        observacao="Inválida"
    )

    with pytest.raises(ValidationError):
        apostila.full_clean()