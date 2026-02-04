import pytest
from apps.usuarios.services.sme_integracao_service import SmeIntegracaoService
from apps.helpers.exceptions import (
    AuthenticationError,
    SmeIntegracaoException,
    InternalError
)
import requests
from rest_framework import status
from unittest.mock import patch, MagicMock


class FakeResponse:
    def __init__(self, status, data=None):
        self.status_code = status
        self._data = data or {}

    def json(self):
        return self._data


def test_sme_autentica_success(monkeypatch):
    def fake_post(*args, **kwargs):
        return FakeResponse(
            200,
            {"nome": "João", "email": "joao@email.com"}
        )

    monkeypatch.setattr(requests, "post", fake_post)

    result = SmeIntegracaoService.autentica("1234", "senha")

    assert result["nome"] == "João"


def test_sme_autentica_unauthorized(monkeypatch):
    def fake_post(*args, **kwargs):
        return FakeResponse(401)

    monkeypatch.setattr(requests, "post", fake_post)

    with pytest.raises(AuthenticationError):
        SmeIntegracaoService.autentica("1234", "errada")


def test_sme_autentica_other_status(monkeypatch):
    def fake_post(*args, **kwargs):
        return FakeResponse(500)

    monkeypatch.setattr(requests, "post", fake_post)

    with pytest.raises(SmeIntegracaoException):
        SmeIntegracaoService.autentica("1234", "senha")


def test_sme_autentica_request_exception(monkeypatch):
    def fake_post(*args, **kwargs):
        raise requests.exceptions.RequestException("timeout")

    monkeypatch.setattr(requests, "post", fake_post)

    with pytest.raises(SmeIntegracaoException):
        SmeIntegracaoService.autentica("1234", "senha")


def test_sme_autentica_internal_error(monkeypatch):
    def fake_post(*args, **kwargs):
        raise ValueError("erro inesperado")

    monkeypatch.setattr(requests, "post", fake_post)

    with pytest.raises(InternalError):
        SmeIntegracaoService.autentica("1234", "senha")


def test_informacao_usuario_sgp_success():
    """Testa quando a API retorna 200 com dados"""
    with patch('requests.get') as mock_get:
        mock_response = MagicMock(status_code=200)
        mock_response.json.return_value = {"email": "teste@email.com"}
        mock_get.return_value = mock_response
        
        result = SmeIntegracaoService.informacao_usuario_sgp("1234567")
        
        assert result == {"email": "teste@email.com"}
        mock_get.assert_called_once()


def test_informacao_usuario_sgp_not_found():
    """Testa quando a API retorna 404"""
    with patch('requests.get') as mock_get:
        mock_response = MagicMock(status_code=404)
        mock_get.return_value = mock_response
        
        with pytest.raises(SmeIntegracaoException) as exc:
            SmeIntegracaoService.informacao_usuario_sgp("1234567")
        
        assert "Dados não encontrados" in str(exc.value)


def test_informacao_usuario_sgp_other_error_status():
    """Testa quando a API retorna outro erro (ex: 500)"""
    with patch('requests.get') as mock_get:
        mock_response = MagicMock(status_code=500)
        mock_get.return_value = mock_response
        
        with pytest.raises(SmeIntegracaoException) as exc:
            SmeIntegracaoService.informacao_usuario_sgp("1234567")


def test_informacao_usuario_sgp_connection_error():
    """Testa quando há erro de conexão"""
    with patch('requests.get') as mock_get:
        mock_get.side_effect = requests.exceptions.ConnectionError
        
        with pytest.raises(requests.exceptions.RequestException):
            SmeIntegracaoService.informacao_usuario_sgp("1234567")


def test_redefine_senha_success(monkeypatch):
    """Testa quando a redefinição de senha ocorre com sucesso"""
    def fake_post(*args, **kwargs):
        return FakeResponse(200)

    monkeypatch.setattr(requests, "post", fake_post)

    result = SmeIntegracaoService.redefine_senha("123456", "NovaSenha123")

    assert result == "OK"


def test_redefine_senha_invalid_data_sem_mock():
    with pytest.raises(SmeIntegracaoException):
        SmeIntegracaoService.redefine_senha("", "NovaSenha123")

    with pytest.raises(SmeIntegracaoException):
        SmeIntegracaoService.redefine_senha("123456", "")


def test_redefine_senha_server_error(monkeypatch):
    """Testa quando a API do SME retorna erro 500"""
    def fake_post(*args, **kwargs):
        return FakeResponse(500)

    monkeypatch.setattr(requests, "post", fake_post)

    with pytest.raises(SmeIntegracaoException):
        SmeIntegracaoService.redefine_senha("123456", "NovaSenha123")


def test_redefine_senha_request_exception(monkeypatch):
    """Testa quando há uma exceção de requisição"""
    def fake_post(*args, **kwargs):
        raise requests.exceptions.RequestException("timeout")

    monkeypatch.setattr(requests, "post", fake_post)

    with pytest.raises(SmeIntegracaoException):
        SmeIntegracaoService.redefine_senha("123456", "NovaSenha123")


def test_redefine_senha_internal_error(monkeypatch):
    """Testa quando ocorre um erro inesperado"""
    def fake_post(*args, **kwargs):
        raise ValueError("erro inesperado")

    monkeypatch.setattr(requests, "post", fake_post)

    with pytest.raises(SmeIntegracaoException):
        SmeIntegracaoService.redefine_senha("123456", "NovaSenha123")


def test_redefine_senha_bad_request_with_message():
    """Cobre o bloco else que extrai mensagem do response.content"""
    with patch('requests.post') as mock_post:
        mock_response = MagicMock()
        mock_response.status_code = 400
        mock_response.content = b'{"Erro":"Senha invalida"}'
        mock_post.return_value = mock_response
        
        with pytest.raises(SmeIntegracaoException) as exc:
            SmeIntegracaoService.redefine_senha("123456", "SenhaRuim")
        
        assert "Senha invalida" in str(exc.value)

@patch("apps.usuarios.services.sme_integracao_service.requests.post")
class TestAlteraEmail:

    def test_sucesso(self, mock_post):
        """Deve retornar OK quando a API responde 200"""
        mock_response = MagicMock()
        mock_response.status_code = status.HTTP_200_OK
        mock_post.return_value = mock_response

        result = SmeIntegracaoService.altera_email("1234567", "teste@sme.prefeitura.sp.gov.br")

        assert result == "OK"
        mock_post.assert_called_once()

    def test_parametros_invalidos(self, mock_post):
        """Deve lançar exceção se registro_funcional ou email forem vazios"""
        with pytest.raises(SmeIntegracaoException) as exc:
            SmeIntegracaoService.altera_email("", "teste@sme.prefeitura.sp.gov.br")
        assert "Registro funcional e email são obrigatórios" in str(exc.value)

        with pytest.raises(SmeIntegracaoException):
            SmeIntegracaoService.altera_email("1234567", "")

        mock_post.assert_not_called()

    def test_erro_api(self, mock_post):
        """Deve lançar exceção quando API responde status != 200"""
        mock_response = MagicMock()
        mock_response.status_code = 400
        mock_response.content = b'{"mensagem":"Erro API"}'
        mock_post.return_value = mock_response

        with pytest.raises(SmeIntegracaoException) as exc:
            SmeIntegracaoService.altera_email("1234567", "teste@sme.prefeitura.sp.gov.br")

        assert "Erro API" in str(exc.value)
        mock_post.assert_called_once()

    def test_excecao_generica(self, mock_post):
        """Deve encapsular erros inesperados em SmeIntegracaoException"""
        mock_post.side_effect = requests.RequestException("Falha de rede")

        with pytest.raises(SmeIntegracaoException) as exc:
            SmeIntegracaoService.altera_email("1234567", "teste@sme.prefeitura.sp.gov.br")

        assert "Falha de rede" in str(exc.value)
        mock_post.assert_called_once()


class TestDesignacao:

    def test_consulta_cargos_funcionario_sem_registro(self):
        """Deve lançar exceção se RF não for informado"""
        with pytest.raises(SmeIntegracaoException) as exc:
            SmeIntegracaoService.consulta_cargos_funcionario("")

        assert "Registro funcional é obrigatório" in str(exc.value)


    def test_consulta_cargos_funcionario_success(self):
        """Deve retornar lista de cargos quando API responde 200"""
        cargos_mock = [
            {
                "cargoBase": "Professor",
                "cargoSobreposto": None,
                "funcaoAtividade": "Docência"
            }
        ]

        with patch("apps.usuarios.services.sme_integracao_service.requests.get") as mock_get:
            mock_response = MagicMock()
            mock_response.status_code = status.HTTP_200_OK
            mock_response.json.return_value = cargos_mock
            mock_get.return_value = mock_response

            result = SmeIntegracaoService.consulta_cargos_funcionario("123456")

            assert result == cargos_mock
            mock_get.assert_called_once()


    def test_consulta_cargos_funcionario_status_invalido(self):
        """Deve lançar exceção quando API retorna status diferente de 200"""
        with patch("apps.usuarios.services.sme_integracao_service.requests.get") as mock_get:
            mock_response = MagicMock()
            mock_response.status_code = status.HTTP_500_INTERNAL_SERVER_ERROR
            mock_response.text = "Erro interno"
            mock_get.return_value = mock_response

            with pytest.raises(SmeIntegracaoException) as exc:
                SmeIntegracaoService.consulta_cargos_funcionario("123456")

            assert "Erro ao consultar cargos do servidor" in str(exc.value)
            mock_get.assert_called_once()


    def test_consulta_cargos_funcionario_request_exception(self):
        """Deve lançar exceção quando ocorre erro de comunicação"""
        with patch(
            "apps.usuarios.services.sme_integracao_service.requests.get",
            side_effect=requests.exceptions.RequestException("timeout")
        ):
            with pytest.raises(SmeIntegracaoException) as exc:
                SmeIntegracaoService.consulta_cargos_funcionario("123456")

            assert "Erro de comunicação com SME" in str(exc.value)


class TestBuscarFuncionariosEscolares:

    def test_buscar_funcionarios_escolares_sem_codigo_ue(self):
        """Deve lançar exceção se código da UE não for informado"""
        with pytest.raises(SmeIntegracaoException) as exc:
            SmeIntegracaoService.buscar_funcionarios_escolares("")

        assert "Código da UE é obrigatório" in str(exc.value)

    @patch("apps.usuarios.services.sme_integracao_service.requests.get")
    def test_buscar_funcionarios_escolares_sucesso_200(self, mock_get):
        """Deve retornar lista de cargos com servidores normalizados"""
        mock_get.return_value = MagicMock(
            status_code=status.HTTP_200_OK,
            json=MagicMock(return_value=[
                {
                    "codigoRF": "123456",
                    "nomeServidor": "João da Silva",
                    "dataInicio": "01/01/2020",
                    "dataFim": None,
                    "estaAfastado": False,
                }
            ])
        )

        result = SmeIntegracaoService.buscar_funcionarios_escolares("090450")

        assert isinstance(result, list)
        assert len(result) == len(SmeIntegracaoService.CARGOS_GESTAO_ESCOLAR)

        primeiro_cargo = result[0]
        assert "codigo_cargo" in primeiro_cargo
        assert "nome_cargo" in primeiro_cargo
        assert "servidores" in primeiro_cargo
        assert primeiro_cargo["servidores"][0]["rf"] == "123456"

    @patch("apps.usuarios.services.sme_integracao_service.requests.get")
    def test_buscar_funcionarios_escolares_204_sem_conteudo(self, mock_get):
        """Deve retornar cargo com lista de servidores vazia quando API retorna 204"""
        mock_get.return_value = MagicMock(
            status_code=status.HTTP_204_NO_CONTENT
        )

        result = SmeIntegracaoService.buscar_funcionarios_escolares("090450")

        assert len(result) == len(SmeIntegracaoService.CARGOS_GESTAO_ESCOLAR)

        for cargo in result:
            assert cargo["servidores"] == []

    @patch("apps.usuarios.services.sme_integracao_service.requests.get")
    def test_buscar_funcionarios_escolares_json_invalido(self, mock_get):
        """Deve tratar JSON inválido como lista vazia"""
        mock_response = MagicMock()
        mock_response.status_code = status.HTTP_200_OK
        mock_response.json.side_effect = ValueError("JSON inválido")
        mock_response.text = "erro"
        mock_get.return_value = mock_response

        result = SmeIntegracaoService.buscar_funcionarios_escolares("090450")

        for cargo in result:
            assert cargo["servidores"] == []

    @patch("apps.usuarios.services.sme_integracao_service.requests.get")
    def test_buscar_funcionarios_escolares_status_invalido(self, mock_get):
        """Deve lançar exceção se API retornar status diferente de 200 ou 204"""
        mock_response = MagicMock()
        mock_response.status_code = status.HTTP_500_INTERNAL_SERVER_ERROR
        mock_response.text = "Erro interno"
        mock_get.return_value = mock_response

        with pytest.raises(SmeIntegracaoException) as exc:
            SmeIntegracaoService.buscar_funcionarios_escolares("090450")

        assert "Erro ao buscar funcionários da gestão escolar" in str(exc.value)

    @patch(
        "apps.usuarios.services.sme_integracao_service.requests.get",
        side_effect=requests.exceptions.RequestException("timeout")
    )
    def test_buscar_funcionarios_escolares_request_exception(self, mock_get):
        """Deve lançar exceção quando ocorrer erro de comunicação"""
        with pytest.raises(SmeIntegracaoException) as exc:
            SmeIntegracaoService.buscar_funcionarios_escolares("090450")

        assert "Erro de comunicação com SME" in str(exc.value)
