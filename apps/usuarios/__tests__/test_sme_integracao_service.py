"""Testes do serviço de integração SME.

Este módulo cobre a autenticação SME, consulta de informações de usuário,
redefinição de senha, alteração de e-mail e consulta de cargos de
funcionários, validando os comportamentos esperados em sucessos e
falhas.
"""

from unittest.mock import MagicMock, patch

import pytest
import requests
from rest_framework import status

from apps.designacao.constants.cargos_gestao_escolar import (
    CARGOS_GESTAO_ESCOLAR,
)
from apps.helpers.exceptions import (
    AuthenticationError,
    InternalError,
    SmeIntegracaoError,
)
from apps.usuarios.services.sme_integracao_service import SmeIntegracaoService


class FakeResponse:
    """Resposta falsa para simular chamadas HTTP nos testes."""

    def __init__(self, status, data=None, content=b""):
        """Inicializa resposta mockada com status, dados e conteúdo."""
        self.status_code = status
        self._data = data or {}
        self.content = content
        self.text = content.decode("utf-8") if content else ""

    def json(self):
        """Retorna o corpo JSON simulado da resposta."""
        return self._data


# ---------------------------------------------------------------------------
# autentica
# ---------------------------------------------------------------------------


def test_sme_autentica_success(monkeypatch):
    """Verifica autenticação SME bem-sucedida com resposta 200."""

    def fake_post(*args, **kwargs):
        """Simula resposta HTTP de autenticação bem-sucedida."""
        return FakeResponse(
            200,
            {"nome": "João", "email": "joao@email.com"},
        )

    monkeypatch.setattr(requests, "post", fake_post)

    result = SmeIntegracaoService.autentica(
        "1234",
        "senha",
    )

    assert result["nome"] == "João"


def test_sme_autentica_unauthorized(monkeypatch):
    """Verifica que autenticação inválida gera AuthenticationError."""

    def fake_post(*args, **kwargs):
        """Simula resposta HTTP 401 não autorizada."""
        return FakeResponse(401)

    monkeypatch.setattr(requests, "post", fake_post)

    with pytest.raises(AuthenticationError):
        SmeIntegracaoService.autentica(
            "1234",
            "errada",
        )


def test_sme_autentica_other_status(monkeypatch):
    """Verifica que status inesperado gera SmeIntegracaoError."""

    def fake_post(*args, **kwargs):
        """Simula resposta HTTP com erro interno."""
        return FakeResponse(500)

    monkeypatch.setattr(requests, "post", fake_post)

    with pytest.raises(SmeIntegracaoError):
        SmeIntegracaoService.autentica(
            "1234",
            "senha",
        )


def test_sme_autentica_request_exception(monkeypatch):
    """Verifica que erro de request gera SmeIntegracaoError."""

    def fake_post(*args, **kwargs):
        """Simula exceção de comunicação HTTP."""
        raise requests.exceptions.RequestException("timeout")

    monkeypatch.setattr(requests, "post", fake_post)

    with pytest.raises(SmeIntegracaoError):
        SmeIntegracaoService.autentica(
            "1234",
            "senha",
        )


def test_sme_autentica_internal_error(monkeypatch):
    """Verifica que erro inesperado gera InternalError."""

    def fake_post(*args, **kwargs):
        """Simula exceção inesperada durante autenticação."""
        raise ValueError("erro inesperado")

    monkeypatch.setattr(requests, "post", fake_post)

    with pytest.raises(InternalError):
        SmeIntegracaoService.autentica(
            "1234",
            "senha",
        )


# ---------------------------------------------------------------------------
# informacao_usuario_sgp
# ---------------------------------------------------------------------------


def test_informacao_usuario_sgp_success():
    """Verifica retorno de informações do usuário quando SME responde com sucesso."""
    with patch("requests.get") as mock_get:
        mock_response = MagicMock(status_code=200)
        mock_response.json.return_value = {"email": "teste@email.com"}
        mock_get.return_value = mock_response

        result = SmeIntegracaoService.informacao_usuario_sgp("1234567")
        assert result == {"email": "teste@email.com"}
        mock_get.assert_called_once()


def test_informacao_usuario_sgp_not_found():
    """Verifica que resposta 404 de usuário gera SmeIntegracaoError."""
    with patch("requests.get") as mock_get:
        mock_response = MagicMock(status_code=404)
        mock_get.return_value = mock_response

        with pytest.raises(SmeIntegracaoError) as exc:
            SmeIntegracaoService.informacao_usuario_sgp("1234567")

        assert "Dados não encontrados" in str(exc.value)


def test_informacao_usuario_sgp_other_error_status():
    """Verifica que outros erros HTTP na consulta de usuário geram SmeIntegracaoError."""
    with patch("requests.get") as mock_get:
        mock_response = MagicMock(status_code=500)
        mock_get.return_value = mock_response

        with pytest.raises(SmeIntegracaoError):
            SmeIntegracaoService.informacao_usuario_sgp("1234567")


def test_informacao_usuario_sgp_connection_error():
    """Verifica que erro de conexão ao consultar usuário propaga RequestException."""
    with patch("requests.get") as mock_get:
        mock_get.side_effect = requests.exceptions.ConnectionError

        with pytest.raises(requests.exceptions.RequestException):
            SmeIntegracaoService.informacao_usuario_sgp("1234567")


# ---------------------------------------------------------------------------
# redefine_senha
# ---------------------------------------------------------------------------


def test_redefine_senha_success(monkeypatch):
    """Verifica redefinição de senha SME bem-sucedida."""

    def fake_post(*args, **kwargs):
        """Simula resposta HTTP 200 com sucesso."""
        return FakeResponse(200)

    monkeypatch.setattr(requests, "post", fake_post)
    result = SmeIntegracaoService.redefine_senha("123456", "NovaSenha123")
    assert result == "OK"


def test_redefine_senha_invalid_data_sem_mock():
    """Verifica que dados inválidos na redefinição de senha geram SmeIntegracaoError."""
    with pytest.raises(SmeIntegracaoError):
        SmeIntegracaoService.redefine_senha("", "NovaSenha123")

    with pytest.raises(SmeIntegracaoError):
        SmeIntegracaoService.redefine_senha("123456", "")


def test_redefine_senha_server_error(monkeypatch):
    """Verifica que erro de servidor durante redefinição de senha gera SmeIntegracaoError."""

    def fake_post(*args, **kwargs):
        """Simula resposta HTTP 500 com erro interno."""
        return FakeResponse(500)

    monkeypatch.setattr(requests, "post", fake_post)
    with pytest.raises(SmeIntegracaoError):
        SmeIntegracaoService.redefine_senha("123456", "NovaSenha123")


def test_redefine_senha_request_exception(monkeypatch):
    """Verifica que exceção de requisição na redefinição de senha gera SmeIntegracaoError."""

    def fake_post(*args, **kwargs):
        """Simula resposta HTTP com timeout."""
        raise requests.exceptions.RequestException("timeout")

    monkeypatch.setattr(requests, "post", fake_post)
    with pytest.raises(SmeIntegracaoError):
        SmeIntegracaoService.redefine_senha("123456", "NovaSenha123")


def test_redefine_senha_internal_error(monkeypatch):
    """Verifica que erro interno inesperado na redefinição de senha gera SmeIntegracaoError."""

    def fake_post(*args, **kwargs):
        """Simula resposta HTTP 500 com erro inesperado."""
        raise ValueError("erro inesperado")

    monkeypatch.setattr(requests, "post", fake_post)
    with pytest.raises(SmeIntegracaoError):
        SmeIntegracaoService.redefine_senha("123456", "NovaSenha123")


def test_redefine_senha_bad_request_with_message():
    """Verifica mensagem de erro retornada pelo SME em bad request."""
    with patch("requests.post") as mock_post:
        mock_response = MagicMock()
        mock_response.status_code = 400
        mock_response.content = b'{"Erro":"Senha invalida"}'
        mock_post.return_value = mock_response

        with pytest.raises(SmeIntegracaoError) as exc:
            SmeIntegracaoService.redefine_senha("123456", "SenhaRuim")

        assert "Senha invalida" in str(exc.value)


# ---------------------------------------------------------------------------
# altera_email
# ---------------------------------------------------------------------------


@patch("apps.usuarios.services.sme_integracao_service.requests.post")
class TestAlteraEmail:
    """Testa a operação de alteração de e-mail no serviço SME."""

    def test_sucesso(self, mock_post):
        """Verifica alteração de e-mail SME bem-sucedida."""
        mock_response = MagicMock()
        mock_response.status_code = status.HTTP_200_OK
        mock_post.return_value = mock_response

        result = SmeIntegracaoService.altera_email(
            "1234567", "teste@sme.prefeitura.sp.gov.br"
        )
        assert result == "OK"
        mock_post.assert_called_once()

    def test_parametros_invalidos(self, mock_post):
        """Verifica que parâmetros inválidos para alteração de e-mail geram exceção."""
        with pytest.raises(SmeIntegracaoError) as exc:
            SmeIntegracaoService.altera_email(
                "", "teste@sme.prefeitura.sp.gov.br"
            )
        assert "Registro funcional e email são obrigatórios" in str(exc.value)

        with pytest.raises(SmeIntegracaoError):
            SmeIntegracaoService.altera_email("1234567", "")

        mock_post.assert_not_called()

    def test_erro_api(self, mock_post):
        """Verifica que erro de API SME ao alterar e-mail é reportado corretamente."""
        mock_response = MagicMock()
        mock_response.status_code = 400
        mock_response.content = b'{"mensagem":"Erro API"}'
        mock_post.return_value = mock_response

        with pytest.raises(SmeIntegracaoError) as exc:
            SmeIntegracaoService.altera_email(
                "1234567", "teste@sme.prefeitura.sp.gov.br"
            )

        assert "Erro API" in str(exc.value)
        mock_post.assert_called_once()

    def test_excecao_generica(self, mock_post):
        """Verifica que exceção genérica de rede é capturada como SmeIntegracaoError."""
        mock_post.side_effect = requests.RequestException("Falha de rede")

        with pytest.raises(SmeIntegracaoError) as exc:
            SmeIntegracaoService.altera_email(
                "1234567", "teste@sme.prefeitura.sp.gov.br"
            )

        assert "Falha de rede" in str(exc.value)
        mock_post.assert_called_once()


# ---------------------------------------------------------------------------
# consulta_cargos_funcionario
# ---------------------------------------------------------------------------


class TestConsultaCargos:
    """Testa a consulta de cargos de funcionários no SME."""

    def test_sem_registro_funcional(self):
        """Verifica que ausência de registro funcional gera exceção."""
        with pytest.raises(SmeIntegracaoError) as exc:
            SmeIntegracaoService.consulta_cargos_funcionario("")
        assert "Registro funcional é obrigatório" in str(exc.value)

    @patch("apps.usuarios.services.sme_integracao_service.requests.get")
    def test_sucesso_sem_cd_ue(self, mock_get):
        """Verifica sucesso na consulta de cargos sem cdUeCargoBase nem cdUeCargoSobreposto."""
        cargos_mock = [
            {
                "cargoBase": "Professor",
                "cargoSobreposto": None,
                "funcaoAtividade": "Docência",
                "cdUeCargoBase": None,
                "cdUeCargoSobreposto": None,
            }
        ]
        mock_response = MagicMock()
        mock_response.status_code = status.HTTP_200_OK
        mock_response.json.return_value = cargos_mock
        mock_get.return_value = mock_response

        result = SmeIntegracaoService.consulta_cargos_funcionario("123456")

        assert result == cargos_mock
        mock_get.assert_called_once()

    @patch("apps.usuarios.services.sme_integracao_service.requests.get")
    def test_sucesso_com_cd_ue_base_e_sigla(self, mock_get):
        """Verifica chamada a consulta_informacoes_unidades_escolares quando cdUeCargoBase está preenchido.

        Também verifica que ueCargoBase é prefixado com a sigla retornada.
        """
        cargos_mock = [
            {
                "cdUeCargoBase": "090450",
                "ueCargoBase": "Escola Exemplo",
                "cdUeCargoSobreposto": None,
            }
        ]
        info_ue_mock = {"siglaTipoEscola": "EMEF", "nome": "Escola Exemplo"}

        # Primeira chamada → lista de cargos; segunda → info da UE base
        mock_get.side_effect = [
            MagicMock(
                status_code=status.HTTP_200_OK,
                json=MagicMock(return_value=cargos_mock),
            ),
            MagicMock(
                status_code=status.HTTP_200_OK,
                json=MagicMock(return_value=info_ue_mock),
            ),
        ]

        result = SmeIntegracaoService.consulta_cargos_funcionario("123456")

        assert result[0]["ueCargoBase"] == "EMEF - Escola Exemplo"
        assert mock_get.call_count == 2

    @patch("apps.usuarios.services.sme_integracao_service.requests.get")
    def test_sucesso_com_cd_ue_sobreposto_e_sigla(self, mock_get):
        """Quando cdUeCargoSobreposto está preenchido, deve prefixar ueCargoSobreposto com a sigla."""
        cargos_mock = [
            {
                "cdUeCargoBase": None,
                "cdUeCargoSobreposto": "090451",
                "ueCargoSobreposto": "Escola Sobreposta",
            }
        ]
        info_ue_mock = {"siglaTipoEscola": "EMEI", "nome": "Escola Sobreposta"}

        mock_get.side_effect = [
            MagicMock(
                status_code=status.HTTP_200_OK,
                json=MagicMock(return_value=cargos_mock),
            ),
            MagicMock(
                status_code=status.HTTP_200_OK,
                json=MagicMock(return_value=info_ue_mock),
            ),
        ]

        result = SmeIntegracaoService.consulta_cargos_funcionario("123456")

        assert result[0]["ueCargoSobreposto"] == "EMEI - Escola Sobreposta"
        assert mock_get.call_count == 2

    @patch("apps.usuarios.services.sme_integracao_service.requests.get")
    def test_sucesso_com_cd_ue_base_sem_sigla(self, mock_get):
        """Quando a UE não retorna siglaTipoEscola, ueCargoBase não deve ser alterado."""
        cargos_mock = [
            {
                "cdUeCargoBase": "090450",
                "ueCargoBase": "Escola Exemplo",
                "cdUeCargoSobreposto": None,
            }
        ]
        info_ue_mock = {"siglaTipoEscola": None}

        mock_get.side_effect = [
            MagicMock(
                status_code=status.HTTP_200_OK,
                json=MagicMock(return_value=cargos_mock),
            ),
            MagicMock(
                status_code=status.HTTP_200_OK,
                json=MagicMock(return_value=info_ue_mock),
            ),
        ]

        result = SmeIntegracaoService.consulta_cargos_funcionario("123456")

        assert result[0]["ueCargoBase"] == "Escola Exemplo"

    @patch("apps.usuarios.services.sme_integracao_service.requests.get")
    def test_status_invalido(self, mock_get):
        """Verifica que erro 500 na consulta de cargos gera exceção do SME."""
        mock_response = MagicMock()
        mock_response.status_code = status.HTTP_500_INTERNAL_SERVER_ERROR
        mock_response.text = "Erro interno"
        mock_get.return_value = mock_response

        with pytest.raises(SmeIntegracaoError) as exc:
            SmeIntegracaoService.consulta_cargos_funcionario("123456")

        assert "Erro ao consultar cargos do servidor" in str(exc.value)

    @patch(
        "apps.usuarios.services.sme_integracao_service.requests.get",
        side_effect=requests.exceptions.RequestException("timeout"),
    )
    def test_request_exception(self, mock_get):
        """Verifica que exceção de requisição na consulta de cargos é convertida para SmeIntegracaoError."""
        with pytest.raises(SmeIntegracaoError) as exc:
            SmeIntegracaoService.consulta_cargos_funcionario("123456")

        assert "Erro de comunicação com SME" in str(exc.value)

    @patch("apps.usuarios.services.sme_integracao_service.requests.get")
    def test_sucesso_com_cargo_sobreposto_formatado(self, mock_get):
        """Deve formatar corretamente cargo sobreposto retornado pela integração."""
        cargos_mock = [
            {
                "cargoBase": None,
                "cargoSobreposto": "COORDENADOR - PEDAGÓGICO",
                "cdUeCargoBase": None,
                "cdUeCargoSobreposto": None,
            }
        ]
        mock_get.return_value = MagicMock(
            status_code=status.HTTP_200_OK,
            json=MagicMock(return_value=cargos_mock),
        )

        result = SmeIntegracaoService.consulta_cargos_funcionario("123456")

        assert result[0]["cargoSobreposto"] == "COORDENADOR"


# ---------------------------------------------------------------------------
# buscar_funcionarios_escolares
# ---------------------------------------------------------------------------


class TestBuscarFuncionariosEscolares:
    """Testa a busca de funcionários escolares por unidade escolar."""

    def test_sem_codigo_ue(self):
        """Verifica que ausência de código UE gera exceção."""
        with pytest.raises(SmeIntegracaoError) as exc:
            SmeIntegracaoService.buscar_funcionarios_escolares("")
        assert "Código da UE é obrigatório" in str(exc.value)

    @patch("apps.usuarios.services.sme_integracao_service.requests.get")
    def test_sucesso_200(self, mock_get):
        """Verifica retorno de lista de funcionários escolares com status 200."""
        mock_get.return_value = MagicMock(
            status_code=status.HTTP_200_OK,
            json=MagicMock(
                return_value=[
                    {
                        "codigoRF": "123456",
                        "nomeServidor": "João da Silva",
                        "dataInicio": "01/01/2020",
                        "dataFim": None,
                        "estaAfastado": False,
                    }
                ]
            ),
        )

        result = SmeIntegracaoService.buscar_funcionarios_escolares("090450")

        assert isinstance(result, list)
        assert len(result) == len(CARGOS_GESTAO_ESCOLAR)
        primeiro_cargo = result[0]
        assert "codigo_cargo" in primeiro_cargo
        assert "nome_cargo" in primeiro_cargo
        assert "servidores" in primeiro_cargo
        assert primeiro_cargo["servidores"][0]["rf"] == "123456"

    @patch("apps.usuarios.services.sme_integracao_service.requests.get")
    def test_204_sem_conteudo(self, mock_get):
        """Verifica que resposta 204 retorna lista de servidores vazia."""
        mock_get.return_value = MagicMock(
            status_code=status.HTTP_204_NO_CONTENT
        )

        result = SmeIntegracaoService.buscar_funcionarios_escolares("090450")

        assert len(result) == len(CARGOS_GESTAO_ESCOLAR)
        for cargo in result:
            assert cargo["servidores"] == []

    @patch("apps.usuarios.services.sme_integracao_service.requests.get")
    def test_json_invalido(self, mock_get):
        """Verifica que JSON inválido durante busca de funcionários resulta em lista vazia."""
        mock_response = MagicMock()
        mock_response.status_code = status.HTTP_200_OK
        mock_response.json.side_effect = ValueError("JSON inválido")
        mock_response.text = "erro"
        mock_get.return_value = mock_response

        result = SmeIntegracaoService.buscar_funcionarios_escolares("090450")

        for cargo in result:
            assert cargo["servidores"] == []

    @patch("apps.usuarios.services.sme_integracao_service.requests.get")
    def test_status_invalido(self, mock_get):
        """Verifica que erro 500 na busca de funcionários gera exceção de comunicação."""
        mock_response = MagicMock()
        mock_response.status_code = status.HTTP_500_INTERNAL_SERVER_ERROR
        mock_response.text = "Erro interno"
        mock_get.return_value = mock_response

        with pytest.raises(SmeIntegracaoError) as exc:
            SmeIntegracaoService.buscar_funcionarios_escolares("090450")

        assert "Erro ao buscar funcionários da gestão escolar" in str(
            exc.value
        )

    @patch(
        "apps.usuarios.services.sme_integracao_service.requests.get",
        side_effect=requests.exceptions.RequestException("timeout"),
    )
    def test_request_exception(self, mock_get):
        """Verifica que exceção de requisição ao buscar funcionários é reportada como SmeIntegracaoError."""
        with pytest.raises(SmeIntegracaoError) as exc:
            SmeIntegracaoService.buscar_funcionarios_escolares("090450")

        assert "Erro de comunicação com SME" in str(exc.value)


# ---------------------------------------------------------------------------
# consulta_informacoes_unidades_escolares
# ---------------------------------------------------------------------------


class TestConsultaInformacoesUnidadesEscolares:
    """Testa a consulta de informações de unidades escolares no SME."""

    def test_sem_codigo(self):
        """Verifica que ausência de código de unidade escolar gera exceção."""
        with pytest.raises(SmeIntegracaoError) as exc:
            SmeIntegracaoService.consulta_informacoes_unidades_escolares("")
        assert "Registro funcional é obrigatório" in str(exc.value)

    @patch("apps.usuarios.services.sme_integracao_service.requests.get")
    def test_sucesso(self, mock_get):
        """Verifica retorno de informações da unidade escolar com sucesso."""
        dados_mock = {
            "codigo": "090450",
            "nome": "EMEF Exemplo",
            "endereco": "Rua Teste, 123",
            "bairro": "Centro",
        }
        mock_response = MagicMock()
        mock_response.status_code = status.HTTP_200_OK
        mock_response.json.return_value = dados_mock
        mock_get.return_value = mock_response

        result = SmeIntegracaoService.consulta_informacoes_unidades_escolares(
            "090450"
        )

        assert result == dados_mock
        mock_get.assert_called_once()

    @patch("apps.usuarios.services.sme_integracao_service.requests.get")
    def test_status_invalido(self, mock_get):
        """Verifica que erro 500 ao consultar unidade escolar gera exceção apropriada."""
        mock_response = MagicMock()
        mock_response.status_code = status.HTTP_500_INTERNAL_SERVER_ERROR
        mock_response.text = "Erro interno"
        mock_get.return_value = mock_response

        with pytest.raises(SmeIntegracaoError) as exc:
            SmeIntegracaoService.consulta_informacoes_unidades_escolares(
                "090450"
            )

        assert "Erro ao consultar informações da unidade escolar" in str(
            exc.value
        )
        mock_get.assert_called_once()

    @patch(
        "apps.usuarios.services.sme_integracao_service.requests.get",
        side_effect=requests.exceptions.RequestException("timeout"),
    )
    def test_request_exception(self, mock_get):
        """Verifica que exceção de requisição gera erro de comunicação com SME."""
        with pytest.raises(SmeIntegracaoError) as exc:
            SmeIntegracaoService.consulta_informacoes_unidades_escolares(
                "090450"
            )

        assert "Erro de comunicação com SME" in str(exc.value)


# ---------------------------------------------------------------------------
# buscar_turmas_ue_ano
# ---------------------------------------------------------------------------


class TestBuscarTurmasUeAno:
    """Testa a busca de turmas por UE e ano letivo."""

    def test_falta_parametros(self):
        """Verifica que falta de parâmetros de UE ou ano gera exceção."""
        with pytest.raises(SmeIntegracaoError) as exc:
            SmeIntegracaoService.buscar_turmas_ue_ano("", None)
        assert "Código da UE e ano letivo são obrigatórios" in str(exc.value)

    @patch("apps.usuarios.services.sme_integracao_service.requests.get")
    def test_sucesso(self, mock_get):
        """Verifica que busca de turmas por ano retorna dados esperados."""
        mock_response = MagicMock()
        mock_response.status_code = status.HTTP_200_OK
        mock_response.json.return_value = [
            {"codigoTurma": 1, "nome": "Turma Teste"}
        ]
        mock_get.return_value = mock_response

        resultado = SmeIntegracaoService.buscar_turmas_ue_ano("UE01", 2024)

        assert resultado == [{"codigoTurma": 1, "nome": "Turma Teste"}]
        mock_get.assert_called_once()

    @patch("apps.usuarios.services.sme_integracao_service.requests.get")
    def test_erro_404(self, mock_get):
        """Verifica erro 404 ao buscar turmas resulta em SmeIntegracaoError."""
        mock_response = MagicMock()
        mock_response.status_code = status.HTTP_404_NOT_FOUND
        mock_get.return_value = mock_response

        with pytest.raises(SmeIntegracaoError) as exc:
            SmeIntegracaoService.buscar_turmas_ue_ano("UE01", 2024)

        assert "Erro ao consultar cargos do servidor" in str(exc.value)

    @patch("apps.usuarios.services.sme_integracao_service.requests.get")
    def test_erro_400(self, mock_get):
        """Verifica que erro 400 ao buscar turmas gera exceção de comunicação."""
        mock_response = MagicMock()
        mock_response.status_code = status.HTTP_400_BAD_REQUEST
        mock_get.return_value = mock_response

        with pytest.raises(SmeIntegracaoError) as exc:
            SmeIntegracaoService.buscar_turmas_ue_ano("UE01", 2026)

        assert "Erro ao consultar cargos do servidor" in str(exc.value)

    @patch("apps.usuarios.services.sme_integracao_service.logger")
    @patch("apps.usuarios.services.sme_integracao_service.requests.get")
    def test_request_exception(self, mock_get, mock_logger):
        """Verifica logger e exceção quando há falha de conexão no SME."""
        mock_get.side_effect = requests.exceptions.RequestException(
            "Falha de Conexão"
        )

        with pytest.raises(SmeIntegracaoError) as exc:
            SmeIntegracaoService.buscar_turmas_ue_ano("UE01", 2026)

        assert "Erro de comunicação com SME" in str(exc.value)
        mock_logger.exception.assert_called_with(
            "Erro de comunicação com API de turmas de um ano letivo"
        )


# ---------------------------------------------------------------------------
# buscar_dados_turma
# ---------------------------------------------------------------------------


class TestBuscarDadosTurma:
    """Testa a busca de dados de turma no SME."""

    def test_validacao_id_nulo(self):
        """Verifica que código de turma nulo gera exceção."""
        with pytest.raises(SmeIntegracaoError) as exc:
            SmeIntegracaoService.buscar_dados_turma(None)
        assert "Código da turma é obrigatório" in str(exc.value)

    @patch("apps.usuarios.services.sme_integracao_service.requests.get")
    def test_sucesso(self, mock_get):
        """Verifica retorno de dados válidos da turma para código de turma informado."""
        mock_response = MagicMock()
        mock_response.status_code = status.HTTP_200_OK
        mock_response.json.return_value = {"codigoTurma": 10, "tipoTurno": 1}
        mock_get.return_value = mock_response

        resultado = SmeIntegracaoService.buscar_dados_turma(10)

        assert resultado["tipoTurno"] == 1
        url_chamada = mock_get.call_args[0][0]
        assert "/turmas/10/dados" in url_chamada

    @patch("apps.usuarios.services.sme_integracao_service.requests.get")
    def test_erro_500(self, mock_get):
        """Verifica que erro 500 ao buscar dados da turma gera exceção."""
        mock_response = MagicMock()
        mock_response.status_code = status.HTTP_500_INTERNAL_SERVER_ERROR
        mock_get.return_value = mock_response

        with pytest.raises(SmeIntegracaoError) as exc:
            SmeIntegracaoService.buscar_dados_turma(12345)

        assert "Erro ao consultar cargos do servidor" in str(exc.value)

    @patch("apps.usuarios.services.sme_integracao_service.logger")
    @patch("apps.usuarios.services.sme_integracao_service.requests.get")
    def test_request_exception_com_logger(self, mock_get, mock_logger):
        """Verifica logger em caso de exceção de conexão ao buscar dados da turma."""
        mock_get.side_effect = requests.exceptions.RequestException(
            "Falha na rede"
        )

        with pytest.raises(SmeIntegracaoError) as exc:
            SmeIntegracaoService.buscar_dados_turma(12345)

        assert "Erro de comunicação com SME" in str(exc.value)
        mock_logger.exception.assert_called_once_with(
            "Erro de comunicação com API de dados da turma"
        )


# ---------------------------------------------------------------------------
# buscar_disciplinas_turma
# ---------------------------------------------------------------------------


class TestBuscarDisciplinasTurma:
    """Testa a busca de disciplinas de turma no SME."""

    def test_sem_codigo_turma(self):
        """Verifica que falta de código de turma gera exceção."""
        with pytest.raises(SmeIntegracaoError) as exc:
            SmeIntegracaoService.buscar_disciplinas_turma(None)
        assert "Código da turma é obrigatório" in str(exc.value)

    @patch("apps.usuarios.services.sme_integracao_service.requests.get")
    def test_sucesso_200(self, mock_get):
        """Verifica retorno de lista de disciplinas válidas com status 200."""
        disciplinas_mock = [
            {"disciplina": "Matemática"},
            {"disciplina": "SP INTEGRAL - Atividade"},
        ]
        mock_get.return_value = MagicMock(
            status_code=status.HTTP_200_OK,
            json=MagicMock(return_value=disciplinas_mock),
        )

        resultado = SmeIntegracaoService.buscar_disciplinas_turma(10)

        assert resultado == disciplinas_mock
        mock_get.assert_called_once()
        url_chamada = mock_get.call_args[0][0]
        assert "/funcionarios/turmas/10/disciplinas" in url_chamada

    @patch("apps.usuarios.services.sme_integracao_service.requests.get")
    def test_204_retorna_lista_vazia(self, mock_get):
        """Verifica retorno de lista vazia quando API responde 204."""
        mock_get.return_value = MagicMock(
            status_code=status.HTTP_204_NO_CONTENT
        )

        resultado = SmeIntegracaoService.buscar_disciplinas_turma(10)

        assert resultado == []

    @patch("apps.usuarios.services.sme_integracao_service.requests.get")
    def test_json_invalido_retorna_lista_vazia(self, mock_get):
        """Verifica que JSON inválido retorna lista vazia."""
        mock_response = MagicMock()
        mock_response.status_code = status.HTTP_200_OK
        mock_response.json.side_effect = ValueError("JSON inválido")
        mock_response.text = "erro"
        mock_get.return_value = mock_response

        resultado = SmeIntegracaoService.buscar_disciplinas_turma(10)

        assert resultado == []

    @patch("apps.usuarios.services.sme_integracao_service.requests.get")
    def test_status_invalido_levanta_excecao(self, mock_get):
        """Verifica que status inválido da API gera exceção de comunicação."""
        mock_response = MagicMock()
        mock_response.status_code = status.HTTP_500_INTERNAL_SERVER_ERROR
        mock_response.text = "Erro interno"
        mock_get.return_value = mock_response

        with pytest.raises(SmeIntegracaoError) as exc:
            SmeIntegracaoService.buscar_disciplinas_turma(10)

        assert "Erro de comunicação com SME" in str(exc.value)

    @patch("apps.usuarios.services.sme_integracao_service.logger")
    @patch("apps.usuarios.services.sme_integracao_service.requests.get")
    def test_request_exception(self, mock_get, mock_logger):
        """Verifica log de exceção para falha de conexão na busca de disciplinas."""
        mock_get.side_effect = requests.exceptions.RequestException("timeout")

        with pytest.raises(SmeIntegracaoError) as exc:
            SmeIntegracaoService.buscar_disciplinas_turma(10)

        assert "Erro de comunicação com SME" in str(exc.value)
        mock_logger.exception.assert_called_once_with(
            "Erro de comunicação com API de disciplinas da turma %s",
            10,
        )


# ---------------------------------------------------------------------------
# formatar_cargo
# ---------------------------------------------------------------------------


class TestFormatarCargo:
    """Testa o formato de cargos retornado pelo SME."""

    def test_texto_none_retorna_vazio(self):
        """Verifica que valor None retorna string vazia."""
        assert SmeIntegracaoService.formatar_cargo(None) == ""

    def test_texto_vazio_retorna_vazio(self):
        """Verifica que texto vazio retorna string vazia."""
        assert SmeIntegracaoService.formatar_cargo("") == ""

    def test_texto_com_hifen_retorna_parte_antes(self):
        """Verifica que texto com hífen retorna apenas a parte antes do hífen."""
        assert (
            SmeIntegracaoService.formatar_cargo("DIRETOR - ESCOLA")
            == "DIRETOR"
        )

    def test_texto_sem_hifen_retorna_inteiro(self):
        """Verifica que texto sem hífen é retornado integralmente."""
        assert SmeIntegracaoService.formatar_cargo("PROFESSOR") == "PROFESSOR"
