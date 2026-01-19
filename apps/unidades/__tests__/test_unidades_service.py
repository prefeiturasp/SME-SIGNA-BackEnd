import pytest
from unittest.mock import patch, Mock
import requests
from apps.unidades.services.unidades_service import (
    DREIntegracaoService, 
    UnidadeIntegracaoService,
    EOLIntegrationError,
    EOLTimeoutError,
    EOLCommunicationError,
    EOLUnexpectedResponseError
)


class TestDREIntegracaoService:
    """Testes para o DREIntegracaoService"""
    
    # ==================== TESTES DE get_dres ====================
    
    @patch('apps.unidades.services.unidades_service.requests.get')
    @patch('apps.unidades.services.unidades_service.env')
    def test_get_dres_sucesso(
        self, mock_env, mock_get, 
        mock_env_config, mock_http_response_success, mock_dres_response
    ):
        """Testa busca de DREs com sucesso"""
        mock_env.side_effect = mock_env_config()
        mock_get.return_value = mock_http_response_success(mock_dres_response)
        
        result = DREIntegracaoService.get_dres()
        
        assert result == mock_dres_response
        assert len(result) == 2
        mock_get.assert_called_once()
        assert 'x-api-eol-key' in mock_get.call_args[1]['headers']
    
    @patch('apps.unidades.services.unidades_service.requests.get')
    @patch('apps.unidades.services.unidades_service.env')
    @pytest.mark.parametrize('status_code,exception_type,error_message', [
        (401, PermissionError, 'Não autorizado'),
        (500, EOLIntegrationError, 'Erro na consulta de DREs'),
        (503, EOLIntegrationError, 'Erro na consulta de DREs'),
    ])
    def test_get_dres_erros_http(
        self, mock_env, mock_get, 
        mock_env_config, mock_http_response_error,
        status_code, exception_type, error_message
    ):
        """Testa diferentes erros HTTP ao buscar DREs"""
        mock_env.side_effect = mock_env_config()
        mock_get.return_value = mock_http_response_error(status_code)
        
        with pytest.raises(exception_type) as exc_info:
            DREIntegracaoService.get_dres()
        
        assert error_message in str(exc_info.value)
    
    @patch('apps.unidades.services.unidades_service.requests.get')
    @patch('apps.unidades.services.unidades_service.env')
    @pytest.mark.parametrize('exception_class,expected_exception,error_message', [
        (requests.exceptions.Timeout, EOLTimeoutError, 'Tempo limite excedido'),
        (requests.exceptions.ConnectionError, EOLCommunicationError, 'Erro de comunicação'),
        (requests.exceptions.RequestException, EOLCommunicationError, 'Erro de comunicação'),
    ])
    def test_get_dres_excecoes_requests(
        self, mock_env, mock_get, 
        mock_env_config, exception_class, expected_exception, error_message
    ):
        """Testa diferentes exceções de requests ao buscar DREs"""
        mock_env.side_effect = mock_env_config()
        mock_get.side_effect = exception_class("Erro de teste")
        
        with pytest.raises(expected_exception) as exc_info:
            DREIntegracaoService.get_dres()
        
        assert error_message in str(exc_info.value)
    
    @patch('apps.unidades.services.unidades_service.requests.get')
    @patch('apps.unidades.services.unidades_service.env')
    def test_get_dres_lista_vazia(
        self, mock_env, mock_get, 
        mock_env_config, mock_http_response_success
    ):
        """Testa busca de DREs retornando lista vazia"""
        mock_env.side_effect = mock_env_config()
        mock_get.return_value = mock_http_response_success([])
        
        result = DREIntegracaoService.get_dres()
        
        assert result == []
        assert len(result) == 0
    
    @patch('apps.unidades.services.unidades_service.requests.get')
    @patch('apps.unidades.services.unidades_service.env')
    def test_get_dres_headers_corretos(
        self, mock_env, mock_get, 
        mock_env_config, mock_http_response_success, 
        mock_dres_response, api_token
    ):
        """Testa se os headers corretos são enviados"""
        mock_env.side_effect = mock_env_config(token=api_token)
        mock_get.return_value = mock_http_response_success(mock_dres_response)
        
        DREIntegracaoService.get_dres()
        
        call_kwargs = mock_get.call_args[1]
        assert call_kwargs['headers']['Content-Type'] == 'application/json'
        assert 'x-api-eol-key' in call_kwargs['headers']
        assert call_kwargs['timeout'] == 30
    
    @patch('apps.unidades.services.unidades_service.requests.get')
    @patch('apps.unidades.services.unidades_service.env')
    def test_get_dres_excecao_generica(
        self, mock_env, mock_get, 
        mock_env_config
    ):
        """Testa exceção genérica ao buscar DREs (cobre except Exception)"""
        mock_env.side_effect = mock_env_config()
        mock_get.side_effect = RuntimeError("Erro inesperado no sistema")
        
        with pytest.raises(EOLIntegrationError) as exc_info:
            DREIntegracaoService.get_dres()
        
        assert "Erro inesperado ao buscar DREs" in str(exc_info.value)
    
    # ==================== TESTES DE get_dre_by_codigo ====================
    
    @patch.object(DREIntegracaoService, 'get_dres')
    def test_get_dre_by_codigo_encontrada(
        self, mock_get_dres, 
        mock_dres_response, codigo_dre_valido
    ):
        """Testa busca de DRE por código quando encontrada"""
        mock_get_dres.return_value = mock_dres_response
        
        result = DREIntegracaoService.get_dre_by_codigo(codigo_dre_valido)
        
        assert result is not None
        assert result['codigoDRE'] == codigo_dre_valido
        assert result['nomeDRE'] == 'Diretoria Regional de Educação Butantã'
    
    @patch.object(DREIntegracaoService, 'get_dres')
    def test_get_dre_by_codigo_nao_encontrada(
        self, mock_get_dres, 
        mock_dres_response, codigo_dre_invalido
    ):
        """Testa busca de DRE por código quando não encontrada"""
        mock_get_dres.return_value = mock_dres_response
        
        result = DREIntegracaoService.get_dre_by_codigo(codigo_dre_invalido)
        
        assert result is None
    
    @patch.object(DREIntegracaoService, 'get_dres')
    def test_get_dre_by_codigo_lista_vazia(self, mock_get_dres, codigo_dre_valido):
        """Testa busca de DRE por código em lista vazia"""
        mock_get_dres.return_value = []
        
        result = DREIntegracaoService.get_dre_by_codigo(codigo_dre_valido)
        
        assert result is None
    
    @patch.object(DREIntegracaoService, 'get_dres')
    def test_get_dre_by_codigo_propaga_permission_error(self, mock_get_dres, codigo_dre_valido):
        """Testa propagação de PermissionError ao buscar DRE por código"""
        mock_get_dres.side_effect = PermissionError("Não autorizado")

        with pytest.raises(PermissionError) as exc_info:
            DREIntegracaoService.get_dre_by_codigo(codigo_dre_valido)

        assert "Não autorizado" in str(exc_info.value)
    
    @patch.object(DREIntegracaoService, 'get_dres')
    def test_get_dre_by_codigo_propaga_eol_integration_error(self, mock_get_dres, codigo_dre_valido):
        """Testa propagação de EOLIntegrationError ao buscar DRE por código"""
        mock_get_dres.side_effect = EOLIntegrationError("Erro de integração")

        with pytest.raises(EOLIntegrationError) as exc_info:
            DREIntegracaoService.get_dre_by_codigo(codigo_dre_valido)

        assert "Erro de integração" in str(exc_info.value)
    
    # ==================== TESTES DE LOGGING ====================
    
    @patch('apps.unidades.services.unidades_service.logger')
    @patch('apps.unidades.services.unidades_service.requests.get')
    @patch('apps.unidades.services.unidades_service.env')
    def test_get_dres_logging_sucesso(
        self, mock_env, mock_get, mock_logger,
        mock_env_config, mock_http_response_success, mock_dres_response
    ):
        """Testa logging em caso de sucesso"""
        mock_env.side_effect = mock_env_config()
        mock_get.return_value = mock_http_response_success(mock_dres_response)
        
        DREIntegracaoService.get_dres()
        
        assert mock_logger.info.call_count >= 2
        mock_logger.info.assert_any_call("Buscando DREs no EOL")
    
    @patch('apps.unidades.services.unidades_service.logger')
    @patch('apps.unidades.services.unidades_service.requests.get')
    @patch('apps.unidades.services.unidades_service.env')
    def test_get_dres_logging_erro_401(
        self, mock_env, mock_get, mock_logger,
        mock_env_config, mock_http_response_error
    ):
        """Testa logging em caso de erro 401"""
        mock_env.side_effect = mock_env_config()
        mock_get.return_value = mock_http_response_error(401)
        
        with pytest.raises(PermissionError):
            DREIntegracaoService.get_dres()
        
        assert mock_logger.error.call_count >= 1


class TestUnidadeIntegracaoService:
    """Testes para o UnidadeIntegracaoService"""
    
    # ==================== TESTES DE get_unidades_by_dre ====================
    
    @patch('apps.unidades.services.unidades_service.requests.get')
    @patch('apps.unidades.services.unidades_service.env')
    def test_get_unidades_by_dre_sucesso(
        self, mock_env, mock_get,
        mock_env_config, mock_http_response_success, 
        mock_unidades_response, codigo_dre_valido
    ):
        """Testa busca de unidades por DRE com sucesso"""
        mock_env.side_effect = mock_env_config()
        mock_get.return_value = mock_http_response_success(mock_unidades_response)
        
        result = UnidadeIntegracaoService.get_unidades_by_dre(codigo_dre_valido)
        
        assert result == mock_unidades_response
        assert len(result) == 2
        mock_get.assert_called_once()
        assert codigo_dre_valido in mock_get.call_args[0][0]
    
    @patch('apps.unidades.services.unidades_service.requests.get')
    @pytest.mark.parametrize('codigo_invalido', ['', None, '   '])
    def test_get_unidades_by_dre_codigo_invalido(self, mock_get, codigo_invalido):
        """Testa erro quando código da DRE é inválido"""
        with pytest.raises(ValueError) as exc_info:
            UnidadeIntegracaoService.get_unidades_by_dre(codigo_invalido)
        
        assert "É necessário informar o código da DRE" in str(exc_info.value)
        mock_get.assert_not_called()
    
    @patch('apps.unidades.services.unidades_service.requests.get')
    @patch('apps.unidades.services.unidades_service.env')
    @pytest.mark.parametrize('status_code,exception_type,error_message', [
        (401, PermissionError, 'Não autorizado'),
        (404, LookupError, 'DRE não encontrada'),
        (500, EOLIntegrationError, 'Erro na consulta de UEs por DRE'),
    ])
    def test_get_unidades_by_dre_erros_http(
        self, mock_env, mock_get,
        mock_env_config, mock_http_response_error, codigo_dre_valido,
        status_code, exception_type, error_message
    ):
        """Testa diferentes erros HTTP ao buscar unidades"""
        mock_env.side_effect = mock_env_config()
        mock_get.return_value = mock_http_response_error(status_code)
        
        with pytest.raises(exception_type) as exc_info:
            UnidadeIntegracaoService.get_unidades_by_dre(codigo_dre_valido)
        
        assert error_message in str(exc_info.value)
    
    @patch('apps.unidades.services.unidades_service.requests.get')
    @patch('apps.unidades.services.unidades_service.env')
    @pytest.mark.parametrize('exception_class,expected_exception,error_message', [
        (requests.exceptions.Timeout, EOLTimeoutError, 'Tempo limite excedido'),
        (requests.exceptions.ConnectionError, EOLCommunicationError, 'Erro de comunicação'),
    ])
    def test_get_unidades_by_dre_excecoes_requests(
        self, mock_env, mock_get,
        mock_env_config, codigo_dre_valido,
        exception_class, expected_exception, error_message
    ):
        """Testa diferentes exceções de requests ao buscar unidades"""
        mock_env.side_effect = mock_env_config()
        mock_get.side_effect = exception_class("Erro de teste")
        
        with pytest.raises(expected_exception) as exc_info:
            UnidadeIntegracaoService.get_unidades_by_dre(codigo_dre_valido)
        
        assert error_message in str(exc_info.value)
    
    @patch('apps.unidades.services.unidades_service.requests.get')
    @patch('apps.unidades.services.unidades_service.env')
    def test_get_unidades_by_dre_resposta_nao_lista(
        self, mock_env, mock_get,
        mock_env_config, codigo_dre_valido
    ):
        """Testa erro quando resposta não é uma lista"""
        mock_env.side_effect = mock_env_config()
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {'erro': 'formato inválido'}
        mock_get.return_value = mock_response
        
        with pytest.raises(EOLUnexpectedResponseError) as exc_info:
            UnidadeIntegracaoService.get_unidades_by_dre(codigo_dre_valido)
        
        assert "Resposta inesperada" in str(exc_info.value)
        assert "esperado uma lista" in str(exc_info.value)
    
    @patch('apps.unidades.services.unidades_service.requests.get')
    @patch('apps.unidades.services.unidades_service.env')
    def test_get_unidades_by_dre_url_correta(
        self, mock_env, mock_get,
        mock_env_config, mock_http_response_success,
        mock_unidades_response, api_base_url, codigo_dre_valido
    ):
        """Testa se a URL correta é montada"""
        mock_env.side_effect = mock_env_config(url=api_base_url)
        mock_get.return_value = mock_http_response_success(mock_unidades_response)
        
        UnidadeIntegracaoService.get_unidades_by_dre(codigo_dre_valido)
        
        called_url = mock_get.call_args[0][0]
        assert called_url == f'{api_base_url}/DREs/{codigo_dre_valido}/unidades'
    
    @patch('apps.unidades.services.unidades_service.requests.get')
    @patch('apps.unidades.services.unidades_service.env')
    def test_get_unidades_by_dre_excecao_generica(
        self, mock_env, mock_get,
        mock_env_config, codigo_dre_valido
    ):
        """Testa exceção genérica ao buscar unidades (cobre except Exception)"""
        mock_env.side_effect = mock_env_config()
        mock_get.side_effect = RuntimeError("Erro inesperado no sistema")
        
        with pytest.raises(EOLIntegrationError) as exc_info:
            UnidadeIntegracaoService.get_unidades_by_dre(codigo_dre_valido)
        
        assert "Erro inesperado ao buscar UEs" in str(exc_info.value)
    
    # ==================== TESTES DE LOGGING ====================
    
    @patch('apps.unidades.services.unidades_service.logger')
    @patch('apps.unidades.services.unidades_service.requests.get')
    @patch('apps.unidades.services.unidades_service.env')
    def test_get_unidades_by_dre_logging_sucesso(
        self, mock_env, mock_get, mock_logger,
        mock_env_config, mock_http_response_success,
        mock_unidades_response, codigo_dre_valido
    ):
        """Testa logging em caso de sucesso"""
        mock_env.side_effect = mock_env_config()
        mock_get.return_value = mock_http_response_success(mock_unidades_response)
        
        UnidadeIntegracaoService.get_unidades_by_dre(codigo_dre_valido)
        
        assert mock_logger.info.call_count >= 2
        mock_logger.info.assert_any_call("Buscando UEs da DRE '%s' no EOL", codigo_dre_valido)

    @patch('apps.unidades.services.unidades_service.requests.get')
    @patch('apps.unidades.services.unidades_service.env')
    def test_get_unidades_by_dre_reraise_value_error(
        self, mock_env, mock_get,
        mock_env_config, codigo_dre_valido
    ):
        """
        Testa re-raise de ValueError dentro do bloco try
        (cobre o `except ValueError: raise`)
        """
        mock_env.side_effect = mock_env_config()

        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.side_effect = ValueError("JSON inválido")

        mock_get.return_value = mock_response

        with pytest.raises(ValueError) as exc_info:
            UnidadeIntegracaoService.get_unidades_by_dre(codigo_dre_valido)

        assert "JSON inválido" in str(exc_info.value)