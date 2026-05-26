import pytest
from unittest.mock import patch

from apps.designacao.services.designacao_servidor_service import (
    DesignacaoServidorService,
)
from apps.helpers.exceptions import SmeIntegracaoException


@pytest.mark.django_db
class TestDesignacaoServidorService:

    @patch(
        "apps.designacao.services.designacao_servidor_service."
        "SmeIntegracaoService.consulta_informacoes_unidades_escolares"
    )
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
        mock_consulta_unidade,
    ):
        mock_info_usuario.return_value = {
            "nome": "João da Silva",
            "codigoRf": "0000000",
        }

        mock_consulta_cargos.return_value = [
            {
                "tipoVinculoCargoSobreposto": 1,
                "ueCargoSobreposto": "Escola X",
                "cdCargoSobreposto": 123,
                "cargoSobreposto": "Cargo Sobreposto",
                "cargoBase": "Cargo Base",
                "cdCargoBase": 456,
                "ueCargoBase": "Escola Base",
                "tipoVinculoCargoBase": 2,
                "funcaoAtividade": None,
                "cdUeFuncaoAtividade": None,
                "ueFuncaoAtividade": None,
            }
        ]

        mock_consulta_unidade.return_value = {
            "nomeDRE": "DRE TESTE",
        }

        resultado = DesignacaoServidorService.obter_designacao("0000000")

        assert resultado == {
            "nome_servidor": "João da Silva",
            "nome_civil": "",
            "rf": "0000000",
            "vinculo": 2,
            "cd_cargo_base": 456,
            "cargo_base": "Cargo Base",
            "lotacao": "Escola Base",
            "cd_cargo_sobreposto_funcao_atividade": 123,
            "cargo_sobreposto_funcao_atividade": "Cargo Sobreposto",
            "local_de_exercicio": "Escola X",
            "laudo_medico": "Indisponível",
            "local_de_servico": "Indisponível",
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
            DesignacaoServidorService.obter_designacao("0000000")
