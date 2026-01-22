import pytest
from unittest.mock import patch

from apps.designacao.services.designacao_servidor_service import (
    DesignacaoServidorService
)
from apps.helpers.exceptions import SmeIntegracaoException


@pytest.mark.django_db
class TestDesignacaoServidorService:

    @patch(
        "apps.designacao.services.designacao_servidor_service."
        "SmeIntegracaoService.informacao_usuario_sgp"
    )
    @patch(
        "apps.designacao.services.designacao_servidor_service."
        "SmeIntegracaoService.consulta_cargos_funcionario"
    )
    def test_obter_designacao_sucesso(
        self,
        mock_consulta_cargos,
        mock_info_usuario,
    ):
        mock_info_usuario.return_value = {
            "nome": "João da Silva",
            "codigoRf": "0000000",
        }

        mock_consulta_cargos.return_value = [
            {
                "tipoVinculoCargoSobreposto": 1,
                "ueCargoSobreposto": "Escola X",
                "cargoBase": "Cargo Base",
                "cargoSobreposto": "Cargo Sobreposto",
                "funcaoAtividade": "Função Teste",
            }
        ]

        resultado = DesignacaoServidorService.obter_designacao(
            "0000000"
        )

        assert resultado == {
            "nome": "João da Silva",
            "rf": "0000000",
            "vinculo_cargo_sobreposto": 1,
            "lotacao_cargo_sobreposto": "Escola X",
            "cargo_base": "Cargo Base",
            "cargo_sobreposto": "Cargo Sobreposto",
            "funcao_atividade": "Função Teste",
        }

    def test_obter_designacao_sem_registro_funcional_raises(self):
        with pytest.raises(
            SmeIntegracaoException,
            match="Registro funcional é obrigatório",
        ):
            DesignacaoServidorService.obter_designacao("")

    @patch(
        "apps.designacao.services.designacao_servidor_service."
        "SmeIntegracaoService.informacao_usuario_sgp"
    )
    @patch(
        "apps.designacao.services.designacao_servidor_service."
        "SmeIntegracaoService.consulta_cargos_funcionario"
    )
    def test_obter_designacao_sem_cargos_raises(
        self,
        mock_consulta_cargos,
        mock_info_usuario,
    ):
        mock_info_usuario.return_value = {
            "nome": "João da Silva",
            "codigoRf": "0000000",
        }

        mock_consulta_cargos.return_value = []

        with pytest.raises(
            SmeIntegracaoException,
            match="Servidor não possui cargos",
        ):
            DesignacaoServidorService.obter_designacao(
                "0000000"
            )
