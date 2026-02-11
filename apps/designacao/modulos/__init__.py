from apps.designacao.modulos.lotacao import ModuloLotacaoCalculator
from apps.designacao.modulos.coordenador_pedagogico import (
    ModuloCoordenadorPedagogicoCalculator,
)
from apps.designacao.modulos.supervisor_escolar import (
    ModuloSupervisorEscolarCalculator,
)

Calculadores = {
    "3360": ModuloLotacaoCalculator(),  # Diretor
    "3182": ModuloLotacaoCalculator(),  # Secretário do Diretor
    "3085": ModuloLotacaoCalculator(),  # Assistente do Diretor
    "3379": ModuloCoordenadorPedagogicoCalculator(),
    "3352": ModuloSupervisorEscolarCalculator(),
}
