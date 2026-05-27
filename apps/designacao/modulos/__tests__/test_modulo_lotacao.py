"""Testes para o cálculo de módulo por lotação de cargos escolares.

Cobre as regras de módulo para Diretor, Secretário e Assistente de Diretor
conforme o tipo de escola e a quantidade de classes.
"""

import logging

import pytest

from apps.designacao.modulos.lotacao import ModuloLotacaoCalculator


class TestModuloLotacaoCalculator:
    """Cobertura de teste para regras de lotação de cargos escolares."""

    def setup_method(self):
        """Inicializa a instância de cálculo antes de cada teste."""
        self.calculator = ModuloLotacaoCalculator()

    # ================= DIRETOR =================

    def test_diretor_retorna_um(self):
        """Verifica que o diretor sempre recebe módulo 1."""
        cargo = {"codigo_cargo": "3360"}

        resultado = self.calculator.calcular(cargo, {})

        assert resultado == 1

    # ================= SECRETÁRIO =================

    @pytest.mark.parametrize(
        "sigla_tipo",
        ["EMEBS", "EMEF", "EMEFM", "CIEJA"],
    )
    def test_secretario_tipos_validos_retorna_um(self, sigla_tipo):
        """Verifica que secretários recebem módulo 1 para tipos válidos."""
        cargo = {"codigo_cargo": "3182"}
        informacoes_ue = {"siglaTipoEscola": sigla_tipo}

        resultado = self.calculator.calcular(cargo, informacoes_ue)

        assert resultado == 1

    @pytest.mark.parametrize(
        "sigla_tipo",
        ["CEI", "CEMEI", "EMEI", "DESCONHECIDO", None, ""],
    )
    def test_secretario_tipos_invalidos_retorna_zero(self, sigla_tipo):
        """Verifica que secretários recebem módulo 0 para tipos inválidos."""
        cargo = {"codigo_cargo": "3182"}
        informacoes_ue = {"siglaTipoEscola": sigla_tipo}

        resultado = self.calculator.calcular(cargo, informacoes_ue)

        assert resultado == 0

    # ================= ASSISTENTE =================

    def test_assistente_cei_retorna_um(self):
        """Verifica que assistentes recebem módulo 1 em CEI."""
        cargo = {"codigo_cargo": "3085"}
        informacoes_ue = {"siglaTipoEscola": "CEI"}

        resultado = self.calculator.calcular(cargo, informacoes_ue)

        assert resultado == 1

    @pytest.mark.parametrize(
        "sigla_tipo, qtd_classes, esperado",
        [
            ("CEMEI", 10, 1),
            ("EMEI", 20, 1),
            ("EMEF", 21, 2),
            ("EMEFM", 30, 2),
            ("EMEBS", 1, 1),
        ],
    )
    def test_assistente_por_quantidade_classes(
        self, sigla_tipo, qtd_classes, esperado
    ):
        """Verifica cálculo de módulo do assistente usando quantidade de classes."""
        cargo = {"codigo_cargo": "3085"}
        informacoes_ue = {
            "siglaTipoEscola": f" {sigla_tipo} ",
            "turmas": {"total": qtd_classes},
        }

        resultado = self.calculator.calcular(cargo, informacoes_ue)

        assert resultado == esperado

    def test_assistente_sem_quantidade_classes_retorna_zero_e_log(
        self, caplog
    ):
        """Verifica comportamento de log e retorno quando faltam classes."""
        cargo = {"codigo_cargo": "3085"}
        informacoes_ue = {
            "siglaTipoEscola": "EMEF",
            "turmas": {"total": None},
        }

        with caplog.at_level(logging.WARNING):
            resultado = self.calculator.calcular(cargo, informacoes_ue)

        assert resultado == 0
        assert "Quantidade de classes ausente." in caplog.text

    # ================= DEFAULT =================

    def test_cargo_desconhecido_retorna_zero(self):
        """Verifica que cargos desconhecidos retornam módulo zero."""
        cargo = {"codigo_cargo": "9999"}

        resultado = self.calculator.calcular(cargo, {})

        assert resultado == 0

    @pytest.mark.parametrize(
        "sigla_tipo",
        ["DESCONHECIDO", "", None, "OUTRO_TIPO"],
    )
    def test_assistente_tipo_invalido_retorna_zero(self, sigla_tipo):
        """Verifica que assistente retorna zero com tipo de escola inválido."""
        cargo = {"codigo_cargo": "3085"}
        informacoes_ue = {
            "siglaTipoEscola": sigla_tipo,
            "turmas": {"total": 10},
        }

        resultado = self.calculator.calcular(cargo, informacoes_ue)

        assert resultado == 0
