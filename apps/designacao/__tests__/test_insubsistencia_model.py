import pytest
from django.utils.timezone import now

from apps.designacao.__tests__.factories import criar_designacao
from apps.designacao.models.cessacao import Cessacao
from apps.designacao.models.insubsistencia import Insubsistencia


def _criar_cessacao(designacao):
    return Cessacao.objects.create(
        designacao=designacao,
        numero_portaria="12345",
        ano_vigente="2024",
        sei_numero="999999",
        a_pedido=True,
        data_designacao="2024-03-10",
    )


@pytest.mark.django_db
def test_delete_soft_delete_model():
    designacao = criar_designacao()
    cessacao = _criar_cessacao(designacao)
    insubsistencia = Insubsistencia.objects.create(
        cessacao=cessacao,
        numero_portaria="12345",
        ano_vigente="2024",
        sei_numero="999999",
        doc="DOE",
        observacoes="Teste",
    )

    insubsistencia.delete()
    insubsistencia.refresh_from_db()

    assert insubsistencia.is_deleted is True
    assert insubsistencia.deleted_at is not None
    assert insubsistencia.deleted_at <= now()


@pytest.mark.django_db
def test_defaults_doc_observacoes_e_is_deleted():
    designacao = criar_designacao()
    insubsistencia = Insubsistencia.objects.create(
        designacao=designacao,
        numero_portaria="98765",
        ano_vigente="2024",
        sei_numero="111222",
    )

    assert insubsistencia.doc == ""
    assert insubsistencia.observacoes == ""
    assert insubsistencia.is_deleted is False
    assert insubsistencia.deleted_at is None


def test_meta_db_table():
    assert Insubsistencia._meta.db_table == "insubsistencia"


@pytest.mark.django_db
def test_permite_criacao_com_cessacao():
    designacao = criar_designacao()
    cessacao = _criar_cessacao(designacao)
    insubsistencia = Insubsistencia.objects.create(
        cessacao_id=cessacao.id,
        numero_portaria="22222",
        ano_vigente="2025",
        sei_numero="555666",
    )

    assert insubsistencia.designacao is None
    assert insubsistencia.cessacao_id == cessacao.id


@pytest.mark.django_db
def test_permite_criacao_com_designacao():
    designacao = criar_designacao()
    insubsistencia = Insubsistencia.objects.create(
        designacao_id=designacao.id,
        numero_portaria="22222",
        ano_vigente="2025",
        sei_numero="555666",
    )   

    assert insubsistencia.designacao_id == designacao.id
    assert insubsistencia.cessacao is None


@pytest.mark.django_db
def test_permite_criacao_com_cessacao_e_designacao():
    designacao = criar_designacao()
    cessacao = _criar_cessacao(designacao)
    insubsistencia = Insubsistencia.objects.create(
        cessacao_id=cessacao.id,
        designacao_id=designacao.id,
        numero_portaria="22222",
        ano_vigente="2025",
        sei_numero="555666",    
    )

    assert insubsistencia.designacao_id == designacao.id
    assert insubsistencia.cessacao_id == cessacao.id
    assert insubsistencia.numero_portaria == "22222"
    assert insubsistencia.ano_vigente == "2025"
    assert insubsistencia.sei_numero == "555666"
 