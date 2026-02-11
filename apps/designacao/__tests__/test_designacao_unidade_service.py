from unittest.mock import patch, Mock
from apps.designacao.services.designacao_unidades_service import (
    DesignacaoUnidadeService,
)
from apps.helpers.exceptions import SmeIntegracaoException
from apps.designacao.constants.cargos_gestao_escolar import (
    CARGOS_GESTAO_ESCOLAR
)


class TestDesignacaoUnidadeService:

    @patch(
        "apps.designacao.services.designacao_unidades_service.Calculadores"
    )
    @patch(
        "apps.designacao.services.designacao_unidades_service."
        "SmeIntegracaoService.consulta_informacoes_unidades_escolares"
    )
    @patch(
        "apps.designacao.services.designacao_unidades_service."
        "SmeIntegracaoService.consulta_cargos_funcionario"
    )
    @patch(
        "apps.designacao.services.designacao_unidades_service."
        "SmeIntegracaoService.buscar_funcionarios_escolares"
    )
    def test_obter_informacoes_escolares_sucesso(
        self,
        mock_buscar_funcionarios,
        mock_consulta_cargos,
        mock_consulta_unidade,
        mock_calculadores,
    ):
        mock_buscar_funcionarios.return_value = [
            {
                "codigo_cargo": 1001,
                "nome_cargo": "CARGO_A",
                "servidores": [
                    {
                        "rf": "RF001",
                        "nome": "SERVIDOR_TESTE_1",
                        "esta_afastado": False,
                    }
                ],
            },
            {
                "codigo_cargo": 1002,
                "nome_cargo": "CARGO_B",
                "servidores": [
                    {
                        "rf": "RF002",
                        "nome": "SERVIDOR_TESTE_2",
                        "esta_afastado": False,
                    }
                ],
            },
            {
                "codigo_cargo": 1003,
                "nome_cargo": "CARGO_SEM_SERVIDOR",
                "servidores": [],
            },
        ]

        def side_effect_consulta_cargos(rf):
            if rf == "RF001":
                return [{
                    "cargoSobreposto": "CARGO_SOBREPOSTO_TESTE",
                    "tipoVinculoCargoSobreposto": 3,
                    "ueCargoSobreposto": "UE_TESTE",
                    "cargoBase": "CARGO_BASE_TESTE",
                    "funcaoAtividade": None
                }]
            return []

        mock_consulta_cargos.side_effect = side_effect_consulta_cargos
        mock_consulta_unidade.return_value = {}

        # Nenhum calculator definido → módulo = 0
        mock_calculadores.get.return_value = None

        resultado = DesignacaoUnidadeService.obter_informacoes_escolares(
            "UE_TESTE"
        )

        assert resultado == {
            "cargos": CARGOS_GESTAO_ESCOLAR,
            "funcionarios_unidade": {
                1001: {
                    "codigo_cargo": 1001,
                    "nome_cargo": "CARGO_A",
                    "servidores": [
                        {
                            "rf": "RF001",
                            "nome": "SERVIDOR_TESTE_1",
                            "esta_afastado": False,
                            "cargo_sobreposto": "CARGO_SOBREPOSTO_TESTE",
                            "vinculo_cargo_sobreposto": 3,
                            "lotacao_cargo_sobreposto": "UE_TESTE",
                            "cargo_base": "CARGO_BASE_TESTE",
                            "funcao_atividade": None,
                        }
                    ],
                    "modulo": 0,
                },
                1002: {
                    "codigo_cargo": 1002,
                    "nome_cargo": "CARGO_B",
                    "servidores": [
                        {
                            "rf": "RF002",
                            "nome": "SERVIDOR_TESTE_2",
                            "esta_afastado": False,
                            "cargo_sobreposto": None,
                            "vinculo_cargo_sobreposto": None,
                            "lotacao_cargo_sobreposto": None,
                            "cargo_base": None,
                            "funcao_atividade": None,
                        }
                    ],
                    "modulo": 0,
                },
                1003: {
                    "codigo_cargo": 1003,
                    "nome_cargo": "CARGO_SEM_SERVIDOR",
                    "servidores": [],
                    "modulo": 0,
                },
            },
        }

    @patch(
        "apps.designacao.services.designacao_unidades_service.Calculadores"
    )
    @patch(
        "apps.designacao.services.designacao_unidades_service."
        "SmeIntegracaoService.consulta_informacoes_unidades_escolares"
    )
    @patch(
        "apps.designacao.services.designacao_unidades_service."
        "SmeIntegracaoService.buscar_funcionarios_escolares"
    )
    def test_obter_informacoes_escolares_sem_servidores(
        self,
        mock_buscar_funcionarios,
        mock_consulta_unidade,
        mock_calculadores,
    ):
        mock_buscar_funcionarios.return_value = [
            {
                "codigo_cargo": 9999,
                "nome_cargo": "CARGO_VAZIO",
                "servidores": [],
            }
        ]

        mock_consulta_unidade.return_value = {}
        mock_calculadores.get.return_value = None

        resultado = DesignacaoUnidadeService.obter_informacoes_escolares(
            "UE_TESTE"
        )

        assert resultado == {
            "cargos": CARGOS_GESTAO_ESCOLAR,
            "funcionarios_unidade": {
                9999: {
                    "codigo_cargo": 9999,
                    "nome_cargo": "CARGO_VAZIO",
                    "servidores": [],
                    "modulo": 0,
                }
            },
        }

    @patch(
        "apps.designacao.services.designacao_unidades_service.Calculadores"
    )
    @patch(
        "apps.designacao.services.designacao_unidades_service."
        "SmeIntegracaoService.consulta_informacoes_unidades_escolares"
    )
    @patch(
        "apps.designacao.services.designacao_unidades_service."
        "SmeIntegracaoService.consulta_cargos_funcionario"
    )
    @patch(
        "apps.designacao.services.designacao_unidades_service."
        "SmeIntegracaoService.buscar_funcionarios_escolares"
    )
    def test_obter_informacoes_escolares_consulta_cargos_falha(
        self,
        mock_buscar_funcionarios,
        mock_consulta_cargos,
        mock_consulta_unidade,
        mock_calculadores,
    ):
        mock_buscar_funcionarios.return_value = [
            {
                "codigo_cargo": 2001,
                "nome_cargo": "CARGO_TESTE",
                "servidores": [
                    {
                        "rf": "RF_ERRO",
                        "nome": "SERVIDOR_ERRO",
                        "esta_afastado": False,
                    }
                ],
            }
        ]

        mock_consulta_cargos.side_effect = SmeIntegracaoException(
            "Erro integração SME"
        )

        mock_consulta_unidade.return_value = {}
        mock_calculadores.get.return_value = None

        resultado = DesignacaoUnidadeService.obter_informacoes_escolares(
            "UE_TESTE"
        )

        assert resultado["funcionarios_unidade"][2001]["servidores"][0] == {
            "rf": "RF_ERRO",
            "nome": "SERVIDOR_ERRO",
            "esta_afastado": False,
            "cargo_sobreposto": None,
            "vinculo_cargo_sobreposto": None,
            "lotacao_cargo_sobreposto": None,
            "cargo_base": None,
            "funcao_atividade": None,
        }


    @patch(
        "apps.designacao.services.designacao_unidades_service.Calculadores"
    )
    @patch(
        "apps.designacao.services.designacao_unidades_service."
        "SmeIntegracaoService.consulta_informacoes_unidades_escolares"
    )
    @patch(
        "apps.designacao.services.designacao_unidades_service."
        "SmeIntegracaoService.consulta_cargos_funcionario"
    )
    @patch(
        "apps.designacao.services.designacao_unidades_service."
        "SmeIntegracaoService.buscar_funcionarios_escolares"
    )
    def test_obter_informacoes_escolares_com_calculador_modulo(
        self,
        mock_buscar_funcionarios,
        mock_consulta_cargos,
        mock_consulta_unidade,
        mock_calculadores,
    ):
        # Mock do calculator
        mock_calculator = Mock()
        mock_calculator.calcular.return_value = 5

        mock_calculadores.get.return_value = mock_calculator

        mock_buscar_funcionarios.return_value = [
            {
                "codigo_cargo": 1001,
                "nome_cargo": "CARGO_COM_CALCULADOR",
                "servidores": [
                    {
                        "rf": "RF001",
                        "nome": "SERVIDOR_TESTE_1",
                        "esta_afastado": False,
                    }
                ],
            }
        ]

        mock_consulta_cargos.return_value = []
        mock_consulta_unidade.return_value = {
            "tipoEscola": "EMEF",
            "totalAlunos": 500,
        }

        resultado = DesignacaoUnidadeService.obter_informacoes_escolares(
            "UE_TESTE"
        )

        # Verifica que buscou calculator corretamente
        mock_calculadores.get.assert_called_once_with("1001")

        # Verifica que executou cálculo
        mock_calculator.calcular.assert_called_once_with(
            mock_buscar_funcionarios.return_value[0],
            mock_consulta_unidade.return_value,
        )

        # Verifica módulo calculado
        assert resultado["funcionarios_unidade"][1001]["modulo"] == 5

