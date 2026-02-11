import logging

import pytest

from apps.designacao.modulos.coordenador_pedagogico import (
    ModuloCoordenadorPedagogicoCalculator,
)


class TestModuloCoordenadorPedagogicoCalculator:

    def setup_method(self):
        self.calculator = ModuloCoordenadorPedagogicoCalculator()

    # ================= REGRAS FIXAS =================

    @pytest.mark.parametrize(
        "sigla_tipo, esperado",
        [
            ("CEI", 1),
            ("cei", 1),      # normalização
            (" CEMEI ", 2),  # trim + upper
        ],
    )
    def test_regras_fixas(self, sigla_tipo, esperado):
        informacoes_ue = {
            "siglaTipoEscola": sigla_tipo,
        }

        resultado = self.calculator.calcular({}, informacoes_ue)

        assert resultado == esperado

    # ================= FALTA DE CLASSES =================

    def test_retorna_zero_quando_quantidade_classes_ausente(
        self, caplog
    ):
        informacoes_ue = {
            "siglaTipoEscola": "EMEF",
            "codigoUE": "UE_TESTE",
            "quantidade_classes_api_nova": None,
        }

        with caplog.at_level(logging.WARNING):
            resultado = self.calculator.calcular({}, informacoes_ue)

        assert resultado == 0
        assert (
            "requer quantidade de classes"
            in caplog.text
        )

    # ================= EMEI =================

    @pytest.mark.parametrize(
        "qtd_classes, esperado",
        [
            (10, 1),
            (20, 1),
            (21, 2),
            (30, 2),
        ],
    )
    def test_emef_emiei(self, qtd_classes, esperado):
        informacoes_ue = {
            "siglaTipoEscola": "EMEI",
            "quantidade_classes_api_nova": qtd_classes,
        }

        resultado = self.calculator.calcular({}, informacoes_ue)

        assert resultado == esperado

    # ================= EMEF / EMEBS =================

    @pytest.mark.parametrize(
        "qtd_classes, esperado",
        [
            (10, 1),
            (14, 1),
            (15, 2),
            (35, 2),
            (36, 3),
            (50, 3),
            (51, 4),
        ],
    )
    def test_emef_sem_noturno(self, qtd_classes, esperado):
        informacoes_ue = {
            "siglaTipoEscola": "EMEF",
            "quantidade_classes_api_nova": qtd_classes,
            "possui_turno_noturno": False,
            "quantidade_turmas_noturno": 0,
        }

        resultado = self.calculator.calcular({}, informacoes_ue)

        assert resultado == esperado

    def test_emef_com_noturno_e_5_turmas(self):
        informacoes_ue = {
            "siglaTipoEscola": "EMEF",
            "quantidade_classes_api_nova": 20,
            "possui_turno_noturno": True,
            "quantidade_turmas_noturno": 5,
        }

        resultado = self.calculator.calcular({}, informacoes_ue)

        assert resultado == 3

    def test_emebs_mesmas_regras_do_emef(self):
        informacoes_ue = {
            "siglaTipoEscola": "EMEBS",
            "quantidade_classes_api_nova": 40,
        }

        resultado = self.calculator.calcular({}, informacoes_ue)

        assert resultado == 3

    # ================= DEFAULT =================

    def test_retorna_zero_para_tipo_desconhecido(self):
        informacoes_ue = {
            "siglaTipoEscola": "XPTO",
            "quantidade_classes_api_nova": 10,
        }

        resultado = self.calculator.calcular({}, informacoes_ue)

        assert resultado == 0
