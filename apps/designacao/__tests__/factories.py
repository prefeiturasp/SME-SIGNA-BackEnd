"""Fábrica de objetos de teste para o app designacao.

"""

import datetime

from apps.designacao.models.apostila_detalhe import ApostilaDetalhe
from apps.designacao.models.ato_administrativo import AtoAdministrativo
from apps.designacao.models.cessacao_detalhe import CessacaoDetalhe
from apps.designacao.models.designacao import Designacao
from apps.designacao.models.designacao_detalhe import DesignacaoDetalhe
from apps.designacao.models.insubsistencia_detalhe import InsubsistenciaDetalhe

_ATO = frozenset({"numero_portaria", "ano_vigente", "sei_numero", "doc"})


def criar_ato_designacao(**kwargs):
    """Método criar ato designacao."""
    ato_kwargs = {k: v for k, v in kwargs.items() if k in _ATO}
    detalhe_kwargs = {k: v for k, v in kwargs.items() if k not in _ATO}

    ato = AtoAdministrativo.objects.create(
        tipo=AtoAdministrativo.Tipo.DESIGNACAO,
        numero_portaria=ato_kwargs.get("numero_portaria", "123"),
        ano_vigente=ato_kwargs.get("ano_vigente", "2024"),
        sei_numero=ato_kwargs.get("sei_numero", "SEI-1"),
        doc=ato_kwargs.get("doc"),
    )

    detalhe_base = {
        "dre_nome": "DRE Teste",
        "unidade_proponente": "Escola Teste",
        "codigo_hierarquico": "001",
        "indicado_nome_civil": "Nome Civil",
        "indicado_nome_servidor": "Nome Servidor",
        "indicado_rf": "1234567",
        "indicado_vinculo": 1,
        "indicado_cargo_base": "Cargo Base",
        "indicado_lotacao": "Lotacao",
        "indicado_local_exercicio": "Local",
        "data_inicio": datetime.date(2024, 1, 1),
        "tipo_vaga": DesignacaoDetalhe.TipoVaga.VAGO,
    }
    detalhe_base.update(detalhe_kwargs)
    DesignacaoDetalhe.objects.create(ato=ato, **detalhe_base)
    return ato


# Alias mantido para compatibilidade com testes que usam criar_designacao()
def criar_designacao(**kwargs):
    """Método criar designacao."""
    return criar_ato_designacao(**kwargs)


def criar_designacao_legado(**kwargs):
    """Método criar designacao legado."""
    base = {
        "dre_nome": "DRE Teste",
        "unidade_proponente": "Escola Teste",
        "codigo_hierarquico": "001",
        "ue": "000001",
        "dre": "000001",
        "funcionarios_da_unidade": "10",
        "indicado_nome_servidor": "Nome Servidor",
        "indicado_rf": "1234567",
        "indicado_vinculo": 1,
        "indicado_cargo_base": "Cargo Base",
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


def criar_ato_cessacao(ato_pai, **kwargs):
    """Método criar ato cessacao."""
    ato_kwargs = {k: v for k, v in kwargs.items() if k in _ATO}
    detalhe_kwargs = {k: v for k, v in kwargs.items() if k not in _ATO}

    ato = AtoAdministrativo.objects.create(
        tipo=AtoAdministrativo.Tipo.CESSACAO,
        ato_pai=ato_pai,
        numero_portaria=ato_kwargs.get("numero_portaria", "456"),
        ano_vigente=ato_kwargs.get("ano_vigente", "2024"),
        sei_numero=ato_kwargs.get("sei_numero", "SEI-2"),
        doc=ato_kwargs.get("doc"),
    )

    detalhe_base = {
        "a_pedido": False,
        "remocao": False,
        "aposentadoria": False,
        "data_cessacao": datetime.date(2024, 3, 1),
    }
    detalhe_base.update(detalhe_kwargs)
    CessacaoDetalhe.objects.create(ato=ato, **detalhe_base)
    return ato


def criar_ato_apostila(ato_pai, observacao="Obs", **kwargs):
    """Método criar ato apostila."""
    ato_kwargs = {k: v for k, v in kwargs.items() if k in _ATO}

    ato = AtoAdministrativo.objects.create(
        tipo=AtoAdministrativo.Tipo.APOSTILA,
        ato_pai=ato_pai,
        sei_numero=ato_kwargs.get("sei_numero", "SEI-A"),
        doc=ato_kwargs.get("doc"),
    )
    ApostilaDetalhe.objects.create(ato=ato, observacao=observacao)
    return ato


def criar_ato_insubsistencia(ato_pai, **kwargs):
    """Método criar ato insubsistencia."""
    ato_kwargs = {k: v for k, v in kwargs.items() if k in _ATO}

    ato = AtoAdministrativo.objects.create(
        tipo=AtoAdministrativo.Tipo.INSUBSISTENCIA,
        ato_pai=ato_pai,
        numero_portaria=ato_kwargs.get("numero_portaria", "789"),
        ano_vigente=ato_kwargs.get("ano_vigente", "2024"),
        sei_numero=ato_kwargs.get("sei_numero", "SEI-I"),
        doc=ato_kwargs.get("doc"),
    )
    InsubsistenciaDetalhe.objects.create(
        ato=ato, observacoes=kwargs.get("observacoes", "")
    )
    return ato
