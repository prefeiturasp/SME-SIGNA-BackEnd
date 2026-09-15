"""Testes para o cálculo de módulo do Coordenador Pedagógico.

Verifica as regras de cálculo aplicadas ao cargo 3379 para diferentes tipos
de escola e cenários de quantidade de classes.
"""

import logging

import pytest

from apps.designacao.modulos.coordenador_pedagogico import (
    ModuloCoordenadorPedagogicoCalculator,
)


class TestModuloCoordenadorPedagogicoCalculator:
    """Cobertura de teste para os casos de cálculo do módulo."""

    def setup_method(self):
        """Inicializa a calculadora antes de cada teste."""
        self.calculator = ModuloCoordenadorPedagogicoCalculator()

    # ================= REGRAS FIXAS =================

    @pytest.mark.parametrize(
        "sigla_tipo, esperado",
        [
            ("CEI", 1),
            ("cei", 1),
            (" CEMEI ", 2),
        ],
    )
    def test_regras_fixas(self, sigla_tipo, esperado):
        """Verifica regras fixas de cálculo para tipos específicos de escola.

        Args:
            sigla_tipo: Sigla do tipo de escola.
            esperado: Quantidade esperada de módulos.

        """
        informacoes_ue = {
            "siglaTipoEscola": sigla_tipo,
        }
        resultado = self.calculator.calcular({}, informacoes_ue)
        assert resultado == esperado

    # ================= FALTA DE CLASSES =================

    def test_retorna_zero_quando_quantidade_classes_ausente(self, caplog):
        """Verifica retorno zero quando não há quantidade de classes informada.

        Também valida o registro de mensagem de aviso no log.

        Args:
            caplog: Fixture do pytest para captura de logs.

        """
        informacoes_ue = {
            "siglaTipoEscola": "EMEF",
            "codigoUE": "UE_TESTE",
            "turmas": None,  # Forçando o erro de ausência
        }

        with caplog.at_level(logging.WARNING):
            resultado = self.calculator.calcular({}, informacoes_ue)

        assert resultado == 0
        assert "requer quantidade de classes" in caplog.text

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
        """Verifica cálculo de módulos para escolas do tipo EMEI.

        Args:
            qtd_classes: Quantidade total de classes.
            esperado: Quantidade esperada de módulos.

        """
        informacoes_ue = {
            "siglaTipoEscola": "EMEI",
            "turmas": {"total": qtd_classes, "turnos": []},
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
        """Verifica cálculo de módulos para EMEF sem turmas noturnas.

        Args:
            qtd_classes: Quantidade total de classes.
            esperado: Quantidade esperada de módulos.

        """
        informacoes_ue = {
            "siglaTipoEscola": "EMEF",
            "turmas": {
                "total": qtd_classes,
                "turnos": [{"turno": "Noite", "total": 0}],
            },
        }

        resultado = self.calculator.calcular({}, informacoes_ue)
        assert resultado == esperado

    def test_emef_com_noturno_e_5_turmas(self):
        """Verifica acréscimo de módulo para EMEF com cinco turmas noturnas."""
        informacoes_ue = {
            "siglaTipoEscola": "EMEF",
            "turmas": {
                "total": 20,
                "turnos": [{"turno": "Noite", "total": 5}],
            },
        }

        resultado = self.calculator.calcular({}, informacoes_ue)
        assert resultado == 3

    def test_emef_com_formato_real_de_turnos_do_backend(self):
        """Verifica cálculo usando o formato real de `turmas` do backend.

        Usa o formato retornado por `TurmaService.calcular_turmas`
        (lista `turnos`, não `por_turno`).
        """
        informacoes_ue = {
            "siglaTipoEscola": "EMEF",
            "turmas": {
                "total": 26,
                "turnos": [
                    {"turno": "Manhã", "total": 2},
                    {"turno": "Intermediário", "total": 0},
                    {"turno": "Tarde", "total": 9},
                    {"turno": "Vespertino", "total": 0},
                    {"turno": "Noite", "total": 8},
                    {"turno": "Integral", "total": 7},
                ],
            },
        }

        resultado = self.calculator.calcular({}, informacoes_ue)
        assert resultado == 3

    def test_emebs_mesmas_regras_do_emef(self):
        """Verifica que EMEBS utiliza as mesmas regras de cálculo do EMEF."""
        informacoes_ue = {
            "siglaTipoEscola": "EMEBS",
            "turmas": {"total": 40, "turnos": []},
        }

        resultado = self.calculator.calcular({}, informacoes_ue)
        assert resultado == 3

    # ================= DEFAULT =================

    def test_retorna_zero_para_tipo_desconhecido(self):
        """Verifica retorno zero para tipos de escola não reconhecidos."""
        informacoes_ue = {"siglaTipoEscola": "XPTO", "turmas": {"total": 10}}

        resultado = self.calculator.calcular({}, informacoes_ue)
        assert resultado == 0
