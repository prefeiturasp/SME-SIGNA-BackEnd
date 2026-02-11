import pytest
from unittest.mock import patch
from apps.designacao.services.designacao_unidades_service import DesignacaoUnidadeService
from apps.helpers.exceptions import SmeIntegracaoException

@pytest.mark.django_db
class TestDesignacaoUnidadeService:

    @patch("apps.designacao.services.designacao_unidades_service.SmeIntegracaoService.consulta_cargos_funcionario")
    @patch("apps.designacao.services.designacao_unidades_service.SmeIntegracaoService.buscar_funcionarios_escolares")
    def test_obter_informacoes_escolares_sucesso(self, mock_buscar_funcionarios, mock_consulta_cargos):
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
                ]
            },
            {
                "codigo_cargo": 1002,
                "nome_cargo": "CARGO_B",
                "servidores": [
                    {
                        "rf": "RF002",
                        "nome": "SERVIDOR_TESTE_2",
                        "esta_afastado": False,
                    },
                ]
            },
            {
                "codigo_cargo": 1003,
                "nome_cargo": "CARGO_SEM_SERVIDOR",
                "servidores": []
            }
        ]

        def side_effect_consulta_cargos(rf):
            if rf == "RF001":
                return [{
                    "cargoSobreposto": "CARGO_SOBREPOSTO_TESTE",
                    "tipoVinculoCargoSobreposto": 3,
                    "ueCargoSobreposto": "ANTONIO BRANCO LEFEVRE, PROF.",
                    "cargoBase": "PROF.ED.INF.E ENS.FUND.I - v3",
                    "funcaoAtividade": None
                }]
            else:
                return []

        mock_consulta_cargos.side_effect = side_effect_consulta_cargos

        resultado = DesignacaoUnidadeService.obter_informacoes_escolares("UE_TESTE")

        assert resultado["funcionarios_unidade"] == {
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
                            "lotacao_cargo_sobreposto": "ANTONIO BRANCO LEFEVRE, PROF.",
                            "cargo_base": "PROF.ED.INF.E ENS.FUND.I - v3",
                            "funcao_atividade": None
                        }
                    ],
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
                            "funcao_atividade": None
                        }
                    ],
                },
                1003: {
                    "codigo_cargo": 1003,
                    "nome_cargo": "CARGO_SEM_SERVIDOR",
                    "servidores": [],
                },
        }

        assert mock_buscar_funcionarios.called
        assert mock_consulta_cargos.call_count == 2


    @patch(
        "apps.designacao.services.designacao_unidades_service."
        "SmeIntegracaoService.buscar_funcionarios_escolares"
    )
    def test_obter_informacoes_escolares_sem_servidores(
        self,
        mock_buscar_funcionarios,
    ):
        mock_buscar_funcionarios.return_value = [
            {
                "codigo_cargo": 9999,
                "nome_cargo": "CARGO_VAZIO",
                "servidores": [],
            }
        ]

        resultado = DesignacaoUnidadeService.obter_informacoes_escolares("UE_TESTE")

        assert resultado["funcionarios_unidade"] == {
                9999: {
                    "codigo_cargo": 9999,
                    "nome_cargo": "CARGO_VAZIO",
                    "servidores": [],
                }
        }

    @patch("apps.designacao.services.designacao_unidades_service.SmeIntegracaoService.consulta_cargos_funcionario")
    @patch("apps.designacao.services.designacao_unidades_service.SmeIntegracaoService.buscar_funcionarios_escolares")
    def test_obter_informacoes_escolares_consulta_cargos_falha(self, mock_buscar_funcionarios, mock_consulta_cargos):
        mock_buscar_funcionarios.return_value = [
            {
                "codigo_cargo": 2001,
                "nome_cargo": "CARGO_TESTE",
                "servidores": [{"rf": "RF_ERRO", "nome": "SERVIDOR_ERRO", "esta_afastado": False,}],
            }
        ]

        mock_consulta_cargos.side_effect = SmeIntegracaoException("Erro integração SME")

        resultado = DesignacaoUnidadeService.obter_informacoes_escolares("UE_TESTE")

        assert resultado["funcionarios_unidade"] == {
                2001: {
                    "codigo_cargo": 2001,
                    "nome_cargo": "CARGO_TESTE",
                    "servidores": [
                        {
                            "rf": "RF_ERRO",
                            "nome": "SERVIDOR_ERRO",
                            "esta_afastado": False,
                            "cargo_sobreposto": None,
                            "vinculo_cargo_sobreposto": None,
                            "lotacao_cargo_sobreposto": None,
                            "cargo_base": None,
                            "funcao_atividade": None
                        }
                    ],
                }
        }