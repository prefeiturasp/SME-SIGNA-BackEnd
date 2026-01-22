import logging
import environ
import requests

from apps.helpers.exceptions import (
    AuthenticationError,
    InternalError,
    SmeIntegracaoException
)

from rest_framework import status


env = environ.Env()
logger = logging.getLogger(__name__)

class SmeIntegracaoService:
    """ Serviço responsável por autenticar usuário no CoreSSO (SME) """

    DEFAULT_HEADERS = {
        "accept": "application/json",
        "x-api-eol-key": env("SME_INTEGRACAO_TOKEN", default=""),
    }
    TIMEOUT = 30

    @classmethod
    def autentica(cls, login: str, senha: str) -> dict:
        payload = {
            "usuario": login,
            "senha": senha,
            "codigoSistema": env('CODIGO_SISTEMA_SIGNA', default='')
        }

        url = f"{env('SME_INTEGRACAO_URL', default='')}/v1/autenticacao/externa"

        logger.info("Autenticando no CoreSSO: %s", login)

        try:
            response = requests.post(
                url,
                json=payload,
                headers=cls.DEFAULT_HEADERS,
                timeout=cls.TIMEOUT,
            )

            if response.status_code == 401:
                raise AuthenticationError("Credenciais inválidas")

            if response.status_code != 200:
                raise SmeIntegracaoException(
                    f"Erro ao autenticar no CoreSSO: {response.status_code}"
                )

            return response.json()

        except requests.exceptions.RequestException as e:
            logger.error("Erro de comunicação: %s", e)
            raise SmeIntegracaoException("Erro de comunicação com CoreSSO")

        except (AuthenticationError, SmeIntegracaoException):
            raise

        except Exception as e:
            logger.error("Erro interno na autenticação: %s", e)
            raise InternalError("Erro interno ao autenticar no CoreSSO")
        

    @classmethod
    def informacao_usuario_sgp(cls, username):
        logger.info(f"Consultando dados na API externa para: {username}")
        try:
            url = f"{env('SME_INTEGRACAO_URL', default='')}/AutenticacaoSgp/{username}/dados"  
            response = requests.get(url, headers=cls.DEFAULT_HEADERS, timeout=10)

            if response.status_code == status.HTTP_200_OK:
                return response.json()

            else:
                logger.info(f"Dados não encontrados: {response}")
                raise SmeIntegracaoException('Dados não encontrados.')

        except requests.RequestException:
            logger.exception("Erro de conexão com a API externa")
            raise requests.RequestException("Erro ao conectar-se à API externa.")


    @classmethod
    def redefine_senha(cls, registro_funcional, senha):
        """
        Redefine a senha de um usuário no sistema SME.
        
        IMPORTANTE: Se a nova senha for uma das senhas padrões, a API do SME 
        não permite a atualização. Para resetar para senha padrão, use o endpoint ReiniciarSenha.
        
        Args:
            registro_funcional: Username/registro funcional do usuário
            senha: Nova senha
            
        Returns:
            Dict[str, Any]: Resposta da API ou confirmação de sucesso
            
        Raises:
            SmeIntegracaoException: Em caso de erro na operação
        """

        if not registro_funcional or not senha:
            raise SmeIntegracaoException("Registro funcional e senha são obrigatórios")
        
        logger.info(
            "Iniciando redefinição de senha no CoreSSO para usuário: %s", 
            registro_funcional
        )
        
        data = {
            'Usuario': registro_funcional,
            'Senha': senha
        }

        try:

            url = f"{env('SME_INTEGRACAO_URL', default='')}/AutenticacaoSgp/AlterarSenha"  

            response = requests.post(url, data=data, headers=cls.DEFAULT_HEADERS)

            if response.status_code == status.HTTP_200_OK:
                result = "OK"
                return result
            else:
                texto = response.content.decode('utf-8')
                mensagem = texto.strip("{}'\"")
                logger.info("Erro ao redefinir senha: %s", mensagem)
                raise SmeIntegracaoException(mensagem)
        except Exception as err:
            raise SmeIntegracaoException(str(err))
        

    @classmethod
    def altera_email(cls, registro_funcional, email):
        """
        Altera o email de um usuário no sistema SME.
        
        Args:
            registro_funcional: Username/registro funcional do usuário
            email: Novo Email
            
        Returns:
            Dict[str, Any]: Resposta da API ou confirmação de sucesso
            
        Raises:
            SmeIntegracaoException: Em caso de erro na operação
        """

        if not registro_funcional or not email:
            raise SmeIntegracaoException("Registro funcional e email são obrigatórios")
        
        logger.info(
            "Iniciando alteração de email no CoreSSO para usuário: %s", 
            registro_funcional
        )
        
        data = {
            'Usuario': registro_funcional,
            'Email': email
        }

        try:

            url = f"{env('SME_INTEGRACAO_URL', default='')}/AutenticacaoSgp/AlterarEmail"

            response = requests.post(url, data=data, headers=cls.DEFAULT_HEADERS)

            if response.status_code == status.HTTP_200_OK:
                result = "OK"
                return result
            else:
                texto = response.content.decode('utf-8')
                mensagem = texto.strip("{}'\"")
                logger.info("Erro ao Alterar email: %s", mensagem)
                raise SmeIntegracaoException(mensagem)
        except Exception as err:
            raise SmeIntegracaoException(str(err))
        

    @classmethod
    def consulta_cargos_funcionario(cls, registro_funcional: str) -> list:
        """
        Consulta cargos (base e sobreposto) de um servidor pelo RF.
        """
        if not registro_funcional:
            raise SmeIntegracaoException("Registro funcional é obrigatório")

        logger.info(
            "Consultando cargos do servidor no SME. RF: %s",
            registro_funcional
        )

        try:
            url = (
                f"{env('SME_INTEGRACAO_URL', default='')}/funcionarios/cargo/{registro_funcional}"
            )

            response = requests.get(
                url,
                headers=cls.DEFAULT_HEADERS,
                timeout=cls.TIMEOUT,
            )

            if response.status_code == status.HTTP_200_OK:
                return response.json()

            logger.error(
                "Erro ao consultar cargos. Status: %s | Body: %s",
                response.status_code,
                response.text,
            )
            raise SmeIntegracaoException("Erro ao consultar cargos do servidor")

        except requests.exceptions.RequestException as e:
            logger.exception("Erro de comunicação com API de cargos")
            raise SmeIntegracaoException("Erro de comunicação com SME") from e
