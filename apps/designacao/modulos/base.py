from abc import ABC, abstractmethod

class ModuloCalculator(ABC):

    @abstractmethod
    def calcular(self, cargo: dict, informacoes_ue: dict) -> int:
        pass
