import pytest
from unittest.mock import patch, Mock
from datetime import datetime

from apps.designacao.services.designacao_unidades_service import (
    DesignacaoUnidadeService,
    ModuloService,
    TurmaService
)
from apps.helpers.exceptions import SmeIntegracaoException
from apps.designacao.models import Designacao
from apps.designacao.services.designacao_unidades_service import CicloService


@pytest.mark.django_db
class TestDesignacaoUnidadeService:

    CHAVES_CONTRATO_SERVIDOR = {
        "nome_servidor",
        "nome_civil",
        "rf",
        "vinculo",
        "cargo_base",
        "lotacao",
        "cargo_sobreposto_funcao_atividade",
        "local_de_exercicio",
        "laudo_medico",
        "local_de_servico"
    }

    @patch("apps.designacao.services.designacao_unidades_service.UnidadeIntegracaoService.get_unidades_codigo_integracao_by_dre")
    @patch("apps.designacao.services.designacao_unidades_service.datetime")
    @patch("apps.designacao.services.designacao_unidades_service.Calculadores")
    @patch("apps.designacao.services.designacao_unidades_service.SmeIntegracaoService.buscar_dados_turma")
    @patch("apps.designacao.services.designacao_unidades_service.SmeIntegracaoService.buscar_turmas_ue_ano")
    @patch("apps.designacao.services.designacao_unidades_service.SmeIntegracaoService.consulta_informacoes_unidades_escolares")
    @patch("apps.designacao.services.designacao_unidades_service.SmeIntegracaoService.consulta_cargos_funcionario")
    @patch("apps.designacao.services.designacao_unidades_service.SmeIntegracaoService.buscar_funcionarios_escolares")
    @patch("apps.designacao.services.designacao_unidades_service.SmeIntegracaoService.informacao_usuario_sgp")
    def test_obter_informacoes_escolares_sucesso_completo(
        self,
        mock_usuario,
        mock_buscar_funcionarios,
        mock_consulta_cargos,
        mock_info_ue,
        mock_buscar_turmas,
        mock_dados_turma,
        mock_calculadores,
        mock_datetime,
        mock_unidades
    ):
        mock_datetime.now.return_value = datetime(2024, 5, 20)

        mock_info_ue.return_value = {"tipoEscola": "EMEF", "codigoDRE": "DRE1"}
        mock_calculadores.get.return_value = None

        mock_unidades.return_value = [
            {"codigoUe": "UE123", "codigoIntegracao": "ABC123"}
        ]

        mock_buscar_funcionarios.return_value = [
            {
                "codigo_cargo": 1001,
                "servidores": [{"rf": "RF001"}]
            }
        ]

        mock_usuario.return_value = {"nome": "JOÃO", "codigoRf": "RF001"}

        mock_consulta_cargos.return_value = [{
            "cargoSobreposto": "CARGO_S",
            "tipoVinculoCargoSobreposto": 3,
            "ueCargoSobreposto": "UE_X",
            "cargoBase": "BASE_X",
            "funcaoAtividade": "FUNCAO_X"
        }]

        mock_buscar_turmas.return_value = [
            {"codigoTurma": "T1", "siglaModalidade": "EF", "nomeTurmaEOL": "1º ano"}
        ]

        mock_dados_turma.return_value = {"tipoTurno": 1}

        resultado = DesignacaoUnidadeService.obter_informacoes_escolares("UE123")

        servidor = resultado["funcionarios_unidade"][1001]["servidores"][0]

        assert self.CHAVES_CONTRATO_SERVIDOR.issubset(servidor.keys())

        assert resultado["turmas"]["total"] == 1
        assert len(resultado["turmas"]["turnos"]) > 0
        assert resultado["codigo_hierarquico"] == "ABC123"

    @patch("apps.designacao.services.designacao_unidades_service.UnidadeIntegracaoService.get_unidades_codigo_integracao_by_dre")
    @patch("apps.designacao.services.designacao_unidades_service.datetime")
    @patch("apps.designacao.services.designacao_unidades_service.Calculadores")
    @patch("apps.designacao.services.designacao_unidades_service.SmeIntegracaoService.buscar_turmas_ue_ano")
    @patch("apps.designacao.services.designacao_unidades_service.SmeIntegracaoService.consulta_informacoes_unidades_escolares")
    @patch("apps.designacao.services.designacao_unidades_service.SmeIntegracaoService.consulta_cargos_funcionario")
    @patch("apps.designacao.services.designacao_unidades_service.SmeIntegracaoService.buscar_funcionarios_escolares")
    @patch("apps.designacao.services.designacao_unidades_service.SmeIntegracaoService.informacao_usuario_sgp")
    def test_obter_informacoes_escolares_falha_integracao_servidor(
        self,
        mock_usuario,
        mock_buscar_funcs,
        mock_consulta_cargos,
        mock_info_ue,
        mock_buscar_turmas,
        mock_calculadores,
        mock_datetime,
        mock_unidades
    ):
        mock_datetime.now.return_value = datetime(2024, 1, 1)

        mock_unidades.return_value = []
        mock_buscar_funcs.return_value = [
            {"codigo_cargo": 1001, "servidores": [{"rf": "RF_ERRO"}]}
        ]

        mock_usuario.side_effect = SmeIntegracaoException("Erro SME")
        mock_consulta_cargos.side_effect = SmeIntegracaoException("Erro SME")

        mock_info_ue.return_value = {"codigoDRE": "DRE1"}
        mock_buscar_turmas.return_value = []
        mock_calculadores.get.return_value = None

        resultado = DesignacaoUnidadeService.obter_informacoes_escolares("UE123")

        servidor = resultado["funcionarios_unidade"][1001]["servidores"][0]

        for chave in self.CHAVES_CONTRATO_SERVIDOR:
            if chave == "rf":
                assert servidor["rf"] == "RF_ERRO"
            else:
                assert servidor[chave] is None

    def test_definir_modulo_cargo_com_calculador(self):
        mock_calc = Mock()
        mock_calc.calcular.return_value = 8

        with patch(
            "apps.designacao.services.designacao_unidades_service.Calculadores",
            {"1001": mock_calc}
        ):
            resultado = ModuloService.definir_modulo(
                {"codigo_cargo": "1001"},
                {"totalAlunos": 500}
            )

        assert resultado == 8
        mock_calc.calcular.assert_called_once()

    @patch("apps.designacao.services.designacao_unidades_service.SmeIntegracaoService.buscar_dados_turma")
    @patch("apps.designacao.services.designacao_unidades_service.SmeIntegracaoService.buscar_turmas_ue_ano")
    def test_calcular_turmas_turno_desconhecido(self, mock_buscar_turmas, mock_dados_turma):
        mock_buscar_turmas.return_value = [{"codigoTurma": "999"}]
        mock_dados_turma.return_value = {"tipoTurno": 99}

        resultado = TurmaService.calcular_turmas("UE123")

        assert resultado["total"] == 0

    def test_listar_cargos_vaga_sucesso(self):
        resultado = DesignacaoUnidadeService.listar_cargos_vaga()

        assert isinstance(resultado, list)
        assert len(resultado) == len(Designacao.CargoVaga.choices)

        primeiro_cargo = resultado[0]

        assert "codigoCargo" in primeiro_cargo
        assert "nomeCargo" in primeiro_cargo

        diretor = next(c for c in resultado if c["codigoCargo"] == 3360)

        assert diretor["nomeCargo"] == "DIRETOR DE ESCOLA"


class TestCicloService:

    def test_extrair_numero_com_valor(self):
        assert CicloService.extrair_numero("1º ano") == 1

    def test_extrair_numero_sem_valor(self):
        assert CicloService.extrair_numero("sem numero") is None

    # ========================
    # EF
    # ========================
    def test_ciclo_ef_alfabetizacao(self):
        turma = {"siglaModalidade": "EF", "nomeTurmaEOL": "2º ano"}
        assert CicloService.definir_ciclo_turma(turma) == "alfabetizacao"

    def test_ciclo_ef_interdisciplinar(self):
        turma = {"siglaModalidade": "EF", "nomeTurmaEOL": "5º ano"}
        assert CicloService.definir_ciclo_turma(turma) == "interdisciplinar"

    def test_ciclo_ef_autoral(self):
        turma = {"siglaModalidade": "EF", "nomeTurmaEOL": "8º ano"}
        assert CicloService.definir_ciclo_turma(turma) == "autoral"

    def test_ciclo_ef_sem_numero(self):
        turma = {"siglaModalidade": "EF", "nomeTurmaEOL": "ano desconhecido"}
        assert CicloService.definir_ciclo_turma(turma) == "sem_ciclo"

    # ========================
    # EJA
    # ========================
    def test_ciclo_eja_todos(self):
        mapa = {
            "1º termo": "alfabetizacao",
            "2º termo": "basica",
            "3º termo": "complementar",
            "4º termo": "final",
        }

        for nome, esperado in mapa.items():
            turma = {"siglaModalidade": "EJA", "nomeTurmaEOL": nome}
            assert CicloService.definir_ciclo_turma(turma) == esperado

    def test_ciclo_eja_default(self):
        turma = {"siglaModalidade": "EJA", "nomeTurmaEOL": "5º termo"}
        assert CicloService.definir_ciclo_turma(turma) == "sem_ciclo"

    # ========================
    # EM
    # ========================
    def test_ciclo_em(self):
        turma = {"siglaModalidade": "EM", "nomeTurmaEOL": "2ª série"}
        assert CicloService.definir_ciclo_turma(turma) == "2_serie"

    def test_ciclo_em_sem_numero(self):
        turma = {"siglaModalidade": "EM", "nomeTurmaEOL": "sem serie"}
        assert CicloService.definir_ciclo_turma(turma) == "sem_ciclo"

    # ========================
    # EI
    # ========================
    def test_ciclo_ei_bercario_i(self):
        turma = {"siglaModalidade": "EI", "nomeTurmaEOL": "Berçário I"}
        assert CicloService.definir_ciclo_turma(turma) == "bercario_i"

    def test_ciclo_ei_bercario_ii(self):
        turma = {"siglaModalidade": "EI", "nomeTurmaEOL": "Berçário II"}
        assert CicloService.definir_ciclo_turma(turma) == "bercario_ii"

    def test_ciclo_ei_mini_grupo(self):
        turma = {"siglaModalidade": "EI", "nomeTurmaEOL": "Mini Grupo I"}
        assert CicloService.definir_ciclo_turma(turma) == "mini_grupo_i"

    def test_ciclo_ei_infantil(self):
        turma = {"siglaModalidade": "EI", "nomeTurmaEOL": "Infantil II"}
        assert CicloService.definir_ciclo_turma(turma) == "infantil"

    def test_ciclo_ei_sem_match(self):
        turma = {"siglaModalidade": "EI", "nomeTurmaEOL": "Outro"}
        assert CicloService.definir_ciclo_turma(turma) == "sem_ciclo"

    def test_ciclo_ef_fora_do_intervalo(self):
        turma = {"siglaModalidade": "EF", "nomeTurmaEOL": "10º ano"}
        assert CicloService.definir_ciclo_turma(turma) == "sem_ciclo"

    def test_ciclo_ei_sem_match_total(self):
        turma = {"siglaModalidade": "EI", "nomeTurmaEOL": "Qualquer coisa aleatória"}
        assert CicloService.definir_ciclo_turma(turma) == "sem_ciclo"

    def test_ciclo_ei_mini_grupo_ii(self):
        turma = {"siglaModalidade": "EI", "nomeTurmaEOL": "Mini Grupo II"}
        assert CicloService.definir_ciclo_turma(turma) == "mini_grupo_ii"    

    # ========================
    # Modalidade desconhecida
    # ========================
    def test_modalidade_desconhecida(self):
        turma = {"siglaModalidade": "XYZ", "nomeTurmaEOL": "Teste"}
        assert CicloService.definir_ciclo_turma(turma) == "sem_ciclo"

    # ========================
    # mapear_nome_ciclo
    # ========================
    def test_mapear_nome_ciclo(self):
        assert CicloService.mapear_nome_ciclo("alfabetizacao") == "cicloAlfabetizacao"

    def test_mapear_nome_ciclo_default(self):
        assert CicloService.mapear_nome_ciclo("inexistente") == "semCiclo"
        
class TestFuncaoNormalizar:

    def test_normalizar_none(self):
        from apps.designacao.services.designacao_unidades_service import normalizar
        assert normalizar(None) == ""
          