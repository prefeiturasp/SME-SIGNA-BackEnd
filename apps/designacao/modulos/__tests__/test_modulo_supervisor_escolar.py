"""Testes para o cálculo de módulo do Supervisor Escolar.

Verifica o comportamento do cálculo de módulo com base no código da DRE
para o cargo 3352.
"""

import logging

from apps.designacao.modulos.supervisor_escolar import ModuloSupervisorEscolarCalculator


class TestModuloSupervisorEscolarCalculator:
    """Cobertura de teste para o cálculo do módulo de Supervisor Escolar."""

    def setup_method(self):
        """Inicializa a calculadora antes de cada teste."""
        self.calculator = ModuloSupervisorEscolarCalculator()

    def test_calcular_retorna_modulo_quando_dre_valida(self):
        """Verifica que DRE conhecida retorna o módulo correto."""
        cargo = {
            "codigo_cargo": "3352",
            "nome_cargo": "Supervisor Escolar",
        }

        informacoes_ue = {
            "codigoDRE": "108200",  # Campo Limpo
            "codigoUE": "UE_TESTE",
        }

        resultado = self.calculator.calcular(cargo, informacoes_ue)

        assert resultado == 53

    def test_calcular_retorna_zero_quando_codigo_dre_ausente(self, caplog):
        """Verifica que retorna zero e faz log quando falta o código DRE."""
        cargo = {
            "codigo_cargo": "3352",
        }

        informacoes_ue = {
            "codigoUE": "UE_TESTE",
            "codigoDRE": None,
        }

        with caplog.at_level(logging.WARNING):
            resultado = self.calculator.calcular(cargo, informacoes_ue)

        assert resultado == 0
        assert (
            "Código da DRE ausente ao calcular módulo de Supervisor Escolar"
            in caplog.text
        )

    def test_calcular_retorna_zero_quando_dre_nao_mapeada(self, caplog):
        """Verifica que retorna zero e faz log quando a DRE não está mapeada."""
        cargo = {
            "codigo_cargo": "3352",
        }

        informacoes_ue = {
            "codigoUE": "UE_TESTE",
            "codigoDRE": "999999",  # DRE inexistente
        }

        with caplog.at_level(logging.WARNING):
            resultado = self.calculator.calcular(cargo, informacoes_ue)

        assert resultado == 0
        assert "não possui módulo definido para Supervisor Escolar" in caplog.text
