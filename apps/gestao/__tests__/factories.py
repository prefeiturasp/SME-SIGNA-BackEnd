"""Factories de teste para o app gestao."""

from apps.gestao.models.cargo_base import CargoBase


def criar_cargo_base(**kwargs) -> CargoBase:
    """Cria um cargo base com valores padrão para uso em testes."""
    defaults = {
        "codigo_cargo": "3360",
        "descricao_completa": "DIRETOR DE ESCOLA MUNICIPAL",
        "descricao_resumida": "Diretor de Escola",
        "grupamento": CargoBase.Grupamento.GESTORES_EDUCACAO,
        "situacao_funcional": CargoBase.SituacaoFuncional.EFETIVO,
        "status": CargoBase.Status.ATIVO,
    }
    defaults.update(kwargs)
    return CargoBase.objects.create(**defaults)
