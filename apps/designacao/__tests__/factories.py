import datetime
from apps.designacao.models.designacao import Designacao


def criar_designacao(**kwargs):
    base = {
        "dre_nome": "DRE Teste",
        "unidade_proponente": "Escola Teste",
        "codigo_hierarquico": "001",

        "indicado_nome_civil": "Nome Civil",
        "indicado_nome_servidor": "Nome Servidor",
        "indicado_rf": "1234567",
        "indicado_vinculo": 1,
        "indicado_cargo_base": "Cargo Base",
        "indicado_codigo_cargo_base": None,
        "indicado_lotacao": "Lotacao",
        "indicado_local_exercicio": "Local",

        "numero_portaria": "123",
        "ano_vigente": "2024",
        "sei_numero": "SEI-1",
        "data_inicio": datetime.date(2024, 1, 1),

        "tipo_vaga": Designacao.TipoVaga.VAGO,
    }

    base.update(kwargs)
    return Designacao.objects.create(**base)