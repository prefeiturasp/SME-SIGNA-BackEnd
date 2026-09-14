"""Factories de teste para o app gestao."""

from apps.designacao.models.ato_administrativo import AtoAdministrativo
from apps.gestao.models.cargo_base import CargoBase
from apps.gestao.models.modelo_portaria import ModeloPortaria


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


def criar_modelo_portaria(**kwargs) -> ModeloPortaria:
    """Cria um modelo de portaria com valores padrão para uso em testes."""
    defaults = {
        "tipo_portaria": AtoAdministrativo.Tipo.DESIGNACAO,
        "status": ModeloPortaria.Status.ATIVO,
        "nome_modelo": "Designação diretor de escola",
        "tipo_cargo": ModeloPortaria.TipoCargo.CARGO_VAGO,
        "variaveis": [
            ModeloPortaria.Variavel.NOME_SERVIDOR,
            ModeloPortaria.Variavel.NUMERO_RF,
        ],
        "observacoes": "",
        "texto_portaria": "O Secretário Municipal de Educação designa...",
    }
    defaults.update(kwargs)
    return ModeloPortaria.objects.create(**defaults)
