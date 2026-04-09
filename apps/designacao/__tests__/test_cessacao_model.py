import pytest
from django.utils.timezone import now

from apps.designacao.models.designacao import Designacao
from apps.designacao.models.cessacao import Cessacao


@pytest.mark.django_db
def test_delete_soft_delete_model():
    designacao = Designacao.objects.create(
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

    cessacao = Cessacao.objects.create(
        designacao=designacao,
        numero_portaria="12345",
        ano_vigente="2024",
        sei_numero="999999",
        a_pedido=True,
        data_designacao="2024-03-10"
    )

    # executa delete (soft delete)
    cessacao.delete()

    cessacao.refresh_from_db()

    assert cessacao.is_deleted is True
    assert cessacao.deleted_at is not None
    assert cessacao.deleted_at <= now()