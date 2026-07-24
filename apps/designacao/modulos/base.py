"""Base para calculadoras de módulo de cargos escolares.

Define a interface abstrata para classes que calculam o módulo de
cargos com base nas informações da unidade escolar.
"""

from abc import ABC, abstractmethod


class ModuloCalculator(ABC):
    """Interface base para cálculo de módulo de cargos."""

    @abstractmethod
    def calcular(self, cargo: dict, informacoes_ue: dict) -> int:
        """Calcula o módulo do cargo usando informações da unidade escolar.

        Args:
            cargo: Dicionário com dados do cargo.
            informacoes_ue: Dicionário com informações da unidade escolar.

        Returns:
            int: Módulo calculado para o cargo.

        """
        pass
