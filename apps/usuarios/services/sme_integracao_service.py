import logging
import environ
import requests

from apps.helpers.exceptions import (
    AuthenticationError,
    InternalError,
    SmeIntegracaoException
)

env = environ.Env()
logger = logging.getLogger(__name__)

class SmeIntegracaoService:
    """ Serviço responsável por autenticar usuário no CoreSSO (SME) """

    DEFAULT_HEADERS = {
        "accept": "application/json",
        "x-api-eol-key": env("SME_INTEGRACAO_TOKEN", default=""),
        "Content-Type": "application/json-patch+json",
    }
    TIMEOUT = 30

    @classmethod
    def autentica(cls, login: str, senha: str) -> dict:
        payload = {
            "login": login,
            "senha": senha,
        }

        url = f"{env('SME_INTEGRACAO_URL', default='')}/v1/autenticacao"

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
