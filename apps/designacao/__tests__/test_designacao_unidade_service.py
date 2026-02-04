import pytest
from unittest.mock import patch

from apps.designacao.services.designacao_unidades_service import (
    DesignacaoUnidadeService
)
from apps.helpers.exceptions import SmeIntegracaoException


@pytest.mark.django_db
class TestDesignacaoUnidadeService:

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
    ):
        mock_buscar_funcionarios.return_value = [
            {
                "codigo_cargo": 1001,
                "nome_cargo": "CARGO_A",
                "servidores": [
                    {
                        "rf": "RF001",
                        "nome": "SERVIDOR_TESTE_1",
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
                    },
                    {
                        "rf": "RF003",
                        "nome": "SERVIDOR_TESTE_3",
                    },
                ],
            },
            {
                "codigo_cargo": 1003,
                "nome_cargo": "CARGO_SEM_SERVIDOR",
                "servidores": [],
            },
        ]

        mock_consulta_cargos.return_value = [
            {
                "cargoSobreposto": "CARGO_SOBREPOSTO_TESTE"
            }
        ]

        resultado = (
            DesignacaoUnidadeService
            .obter_informacoes_escolares("UE_TESTE")
        )

        assert resultado == [
            {
                "rf": "RF001",
                "nome": "SERVIDOR_TESTE_1",
                "cargoSobreposto": "CARGO_SOBREPOSTO_TESTE - v1",
            },
            {
                "rf": "RF002",
                "nome": "SERVIDOR_TESTE_2",
                "cargoSobreposto": "CARGO_SOBREPOSTO_TESTE - v1",
            },
            {
                "rf": "RF003",
                "nome": "SERVIDOR_TESTE_3",
                "cargoSobreposto": "CARGO_SOBREPOSTO_TESTE - v1",
            },
        ]

        assert mock_buscar_funcionarios.called
        assert mock_consulta_cargos.call_count == 3


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

        resultado = (
            DesignacaoUnidadeService
            .obter_informacoes_escolares("UE_TESTE")
        )

        assert resultado == []


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
    ):
        mock_buscar_funcionarios.return_value = [
            {
                "codigo_cargo": 2001,
                "nome_cargo": "CARGO_TESTE",
                "servidores": [
                    {
                        "rf": "RF_ERRO",
                        "nome": "SERVIDOR_ERRO",
                    }
                ],
            }
        ]

        mock_consulta_cargos.side_effect = SmeIntegracaoException(
            "Erro integração SME"
        )

        resultado = (
            DesignacaoUnidadeService
            .obter_informacoes_escolares("UE_TESTE")
        )

        assert resultado == [
            {
                "rf": "RF_ERRO",
                "nome": "SERVIDOR_ERRO",
                "cargoSobreposto": None,
            }
        ]
