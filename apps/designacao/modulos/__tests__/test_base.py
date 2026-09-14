"""Testes para a base abstrata de calculadoras de módulo."""

from apps.designacao.modulos.base import ModuloCalculator


class _ModuloCalculatorConcreto(ModuloCalculator):
    """Implementação concreta que delega para a base abstrata."""

    def calcular(self, cargo: dict, informacoes_ue: dict) -> int:
        # Chamada intencional ao corpo trivial do método abstrato, só para
        # cobrir essa linha em testes.
        return super().calcular(cargo, informacoes_ue)  # type: ignore[safe-super]


class TestModuloCalculator:
    """Testes para ModuloCalculator."""

    def test_calcular_base_nao_implementa_logica(self):
        """Verifica que o método abstrato base retorna None."""
        calculadora = _ModuloCalculatorConcreto()
        assert calculadora.calcular({}, {}) is None
