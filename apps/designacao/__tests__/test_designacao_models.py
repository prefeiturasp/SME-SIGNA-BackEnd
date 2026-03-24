import pytest
from datetime import date
from apps.designacao.models import Designacao, ImpedimentoSubstituicao


@pytest.mark.django_db
def test_criar_designacao():
    impedimento = ImpedimentoSubstituicao.objects.get(codigo='LIC_MEDICA')
    
    designacao = Designacao.objects.create(
        dre_nome="DRE TESTE",
        unidade_proponente="Unidade Teste",
        codigo_hierarquico="123",

        indicado_nome_civil="João da Silva",
        indicado_nome_servidor="João da Silva",
        indicado_rf="1234567",
        indicado_vinculo=1,
        indicado_cargo_base="Professor",
        indicado_lotacao="Escola A",
        indicado_local_exercicio="Escola A",

        numero_portaria="123",
        ano_vigente="2024",
        sei_numero="123456789",

        data_inicio=date(2024, 1, 1),

        tipo_vaga=Designacao.TipoVaga.VAGO,
        cargo_vaga=Designacao.CargoVaga.DIRETOR,
        impedimento_substituicao=impedimento
    )

    assert designacao.id is not None
    assert designacao.dre_nome == "DRE TESTE"
    assert designacao.tipo_vaga == Designacao.TipoVaga.VAGO

@pytest.mark.django_db
def test_impedimento_str():
    impedimento = ImpedimentoSubstituicao.objects.create(
        codigo='TESTE',
        descricao='Descrição de teste'
    )

    assert str(impedimento) == 'Descrição de teste'