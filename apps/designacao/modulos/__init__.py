from apps.designacao.modulos.base import ModuloCalculator
from apps.designacao.modulos.coordenador_pedagogico import (
    ModuloCoordenadorPedagogicoCalculator,
)
from apps.designacao.modulos.lotacao import ModuloLotacaoCalculator
from apps.designacao.modulos.supervisor_escolar import (
    ModuloSupervisorEscolarCalculator,
)

Calculadores: dict[str, ModuloCalculator] = {
    "3360": ModuloLotacaoCalculator(),  # Diretor
    "3182": ModuloLotacaoCalculator(),  # Secretário do Diretor
    "3085": ModuloLotacaoCalculator(),  # Assistente do Diretor
    "3379": ModuloCoordenadorPedagogicoCalculator(),
    "3352": ModuloSupervisorEscolarCalculator(),
}
