import pytest
from unittest.mock import patch, Mock, MagicMock
from datetime import datetime
from apps.designacao.services.designacao_unidades_service import DesignacaoUnidadeService
from apps.helpers.exceptions import SmeIntegracaoException
from apps.designacao.models import Designacao


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
        mock_datetime             
    ):
        """Teste de caminho feliz: Valida integração, cálculos e contrato de dados."""
        mock_datetime.now.return_value = datetime(2024, 5, 20)
        mock_info_ue.return_value = {"tipoEscola": "EMEF"}
        mock_calculadores.get.return_value = None

        mock_buscar_funcionarios.return_value = [
            {
                "codigo_cargo": 1001,
                "nome_cargo": "DIRETOR",
                "servidores": [{"rf": "RF001", "nome": "JOÃO"}]
            }
        ]

        mock_usuario.return_value = {
            "nome": "JOÃO",
            "codigoRf": "RF001"
        }

        def side_effect_cargos(rf):
            if rf == "RF001":
                return [{
                    "cargoSobreposto": "CARGO_S",
                    "tipoVinculoCargoSobreposto": 3,
                    "ueCargoSobreposto": "UE_X",
                    "cargoBase": "BASE_X",
                    "funcaoAtividade": "FUNCAO_X"
                }]
            return []
        mock_consulta_cargos.side_effect = side_effect_cargos

        mock_buscar_turmas.return_value = [{"codigoTurma": "TURMA01"}]
        mock_dados_turma.return_value = {"tipoTurno": 1}

        resultado = DesignacaoUnidadeService.obter_informacoes_escolares("UE123")

        mock_buscar_turmas.assert_called_with("UE123", 2024)
        
        servidor = resultado["funcionarios_unidade"][1001]["servidores"][0]
        assert self.CHAVES_CONTRATO_SERVIDOR.issubset(servidor.keys())
        assert servidor["cargo_sobreposto_funcao_atividade"] == "CARGO_S"        
        assert resultado["turmas"]["total"] == 1
        assert resultado["turmas"]["por_turno"]["manhã"] == 1

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
        mock_datetime          
    ):
        """Valida que o sistema não quebra se a integração de um RF específico falhar."""
        mock_datetime.now.return_value = datetime(2024, 1, 1)
        
        mock_buscar_funcs.return_value = [
            {"codigo_cargo": 1001, "servidores": [{"rf": "RF_ERRO"}]}
        ]
        
        mock_usuario.side_effect = SmeIntegracaoException("Erro SME") 
        mock_consulta_cargos.side_effect = SmeIntegracaoException("Erro SME")
        
        mock_info_ue.return_value = {}
        mock_buscar_turmas.return_value = []
        mock_calculadores.get.return_value = None

        resultado = DesignacaoUnidadeService.obter_informacoes_escolares("UE123")

        servidor = resultado["funcionarios_unidade"][1001]["servidores"][0]
        for chave in self.CHAVES_CONTRATO_SERVIDOR:
            if chave != "rf":
                assert servidor[chave] is None
            else:
                assert servidor["rf"] == "RF_ERRO"

    @patch("apps.designacao.services.designacao_unidades_service.Calculadores")
    @patch("apps.designacao.services.designacao_unidades_service.SmeIntegracaoService.consulta_informacoes_unidades_escolares")
    @patch("apps.designacao.services.designacao_unidades_service.SmeIntegracaoService.buscar_funcionarios_escolares")
    def test_definir_modulo_cargo_com_calculador(self, mock_funcs, mock_info_ue, mock_calculadores):
        """Valida a execução da lógica de cálculo de módulo delegada."""
        mock_calc = Mock()
        mock_calc.calcular.return_value = 8
        mock_calculadores.get.return_value = mock_calc
        
        cargo_ue = {"codigo_cargo": "1001"}
        info_ue = {"totalAlunos": 500}
        
        resultado = DesignacaoUnidadeService._definir_modulo_cargo(cargo_ue, info_ue)
        
        assert resultado == 8
        mock_calc.calcular.assert_called_once_with(cargo_ue, info_ue)

    @patch("apps.designacao.services.designacao_unidades_service.SmeIntegracaoService.buscar_dados_turma")
    @patch("apps.designacao.services.designacao_unidades_service.SmeIntegracaoService.buscar_turmas_ue_ano")
    def test_calcular_turmas_turno_desconhecido(self, mock_buscar_turmas, mock_dados_turma):
        """Cobre a linha 'if turno:' garantindo que turnos inválidos não incrementam o dicionário."""
        mock_buscar_turmas.return_value = [{"codigoTurma": "999"}]
        mock_dados_turma.return_value = {"tipoTurno": 99}
        
        resultado = DesignacaoUnidadeService.calcular_turmas("UE123")
        
        assert resultado["total"] == 1
        assert all(count == 0 for count in resultado["por_turno"].values())

    def test_mapear_info_cargo_isolado(self):
        """Teste unitário puro para o mapeamento de campos (Contrato)."""
        dados_sme = {
            "cargoSobreposto": "A",
            "tipoVinculoCargoSobreposto": 1,
            "ueCargoSobreposto": "B",
            "cargoBase": "C",
            "funcaoAtividade": "D"
        }
        resultado = DesignacaoUnidadeService._mapear_info_cargo(dados_sme)
        
        assert resultado["cargo_sobreposto"] == "A"
        assert resultado["vinculo_cargo_sobreposto"] == 1
        assert resultado["lotacao_cargo_sobreposto"] == "B"
        assert resultado["cargo_base"] == "C"
        assert resultado["funcao_atividade"] == "D"


    def test_listar_cargos_vaga_sucesso(self):
        """
        Valida se a listagem de cargos extrai corretamente as 
        informações definidas no IntegerChoices do Model Designacao.
        """

        resultado = DesignacaoUnidadeService.listar_cargos_vaga()

        assert isinstance(resultado, list)
        assert len(resultado) == len(Designacao.CargoVaga.choices)

        primeiro_cargo = resultado[0]

        assert "codigoCargo" in primeiro_cargo
        assert "nomeCargo" in primeiro_cargo
        
        diretor = next(c for c in resultado if c["codigoCargo"] == 3360)

        assert diretor["nomeCargo"] == "DIRETOR DE ESCOLA"

        for cargo in resultado:
            assert isinstance(cargo["codigoCargo"], int)
            assert isinstance(cargo["nomeCargo"], str)