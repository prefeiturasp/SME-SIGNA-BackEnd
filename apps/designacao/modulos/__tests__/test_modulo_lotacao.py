import logging

import pytest

from apps.designacao.modulos.lotacao import (
    ModuloLotacaoCalculator,
)


class TestModuloLotacaoCalculator:

    def setup_method(self):
        self.calculator = ModuloLotacaoCalculator()

    # ================= DIRETOR =================

    def test_diretor_retorna_um(self):
        cargo = {"codigo_cargo": "3360"}

        resultado = self.calculator.calcular(cargo, {})

        assert resultado == 1

    # ================= SECRETÁRIO =================

    @pytest.mark.parametrize(
        "sigla_tipo",
        ["EMEBS", "EMEF", "EMEFM", "CIEJA"],
    )
    def test_secretario_tipos_validos_retorna_um(self, sigla_tipo):
        cargo = {"codigo_cargo": "3182"}
        informacoes_ue = {"siglaTipoEscola": sigla_tipo}

        resultado = self.calculator.calcular(cargo, informacoes_ue)

        assert resultado == 1


    @pytest.mark.parametrize(
        "sigla_tipo",
        ["CEI", "CEMEI", "EMEI", "DESCONHECIDO", None, ""],
    )
    def test_secretario_tipos_invalidos_retorna_zero(self, sigla_tipo):
        cargo = {"codigo_cargo": "3182"}
        informacoes_ue = {"siglaTipoEscola": sigla_tipo}

        resultado = self.calculator.calcular(cargo, informacoes_ue)

        assert resultado == 0


    # ================= ASSISTENTE =================

    def test_assistente_cei_retorna_um(self):
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
        cargo = {"codigo_cargo": "3085"}
        informacoes_ue = {
            "siglaTipoEscola": f" {sigla_tipo} ",
            "quantidade_classes": qtd_classes,
        }

        resultado = self.calculator.calcular(cargo, informacoes_ue)

        assert resultado == esperado

    def test_assistente_sem_quantidade_classes_retorna_zero_e_log(
        self, caplog
    ):
        cargo = {"codigo_cargo": "3085"}
        informacoes_ue = {
            "siglaTipoEscola": "EMEF",
            "quantidade_classes": None,
        }

        with caplog.at_level(logging.WARNING):
            resultado = self.calculator.calcular(cargo, informacoes_ue)

        assert resultado == 0
        assert "Quantidade de classes ausente." in caplog.text

    # ================= DEFAULT =================

    def test_cargo_desconhecido_retorna_zero(self):
        cargo = {"codigo_cargo": "9999"}

        resultado = self.calculator.calcular(cargo, {})

        assert resultado == 0
