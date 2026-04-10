import logging
import requests
import environ
from typing import Dict, List, Optional
from django.conf import settings
from apps.unidades.constants.utils import SUPERVISAO_ESCOLAR_DRES_MAP

env = environ.Env()
logger = logging.getLogger(__name__)

MSG_DRE_OBRIGATORIO = "É necessário informar o código da DRE."
MSG_RESPOSTA_INVALIDA_LISTA = "Resposta inesperada da API (esperado uma lista)."
MSG_DRE_INVALIDO = "dre_codigo não informado ou inválido"

ENV_URL = "SME_INTEGRACAO_URL"

ENDPOINT_DRES = "/DREs"
ENDPOINT_UNIDADES = "/DREs/{}/unidades"
ENDPOINT_ESCOLAS = "/DREs/{}/escola"
ENDPOINT_CODIGO_INTEGRACAO = "/DREs/{}/unidades/codigo-integracao"


# Exceções customizadas
class EOLIntegrationError(Exception):
    pass


class EOLTimeoutError(EOLIntegrationError):
    pass


class EOLCommunicationError(EOLIntegrationError):
    pass


class EOLUnexpectedResponseError(EOLIntegrationError):
    pass


class BaseEOLService:
    DEFAULT_HEADERS = {
        "Content-Type": "application/json",
        "x-api-eol-key": env("SME_INTEGRACAO_TOKEN", default=""),
    }
    DEFAULT_TIMEOUT = 30

    @classmethod
    def _get(cls, url: str, context: str) -> list | dict:
        try:
            logger.info("Iniciando requisição ao EOL: %s", context)

            response = requests.get(
                url,
                headers=cls.DEFAULT_HEADERS,
                timeout=cls.DEFAULT_TIMEOUT,
            )

            if response.status_code == 401:
                logger.error("Não autorizado: %s", context)
                raise PermissionError("Não autorizado ao sistema EOL")

            if response.status_code == 404:
                logger.warning("Recurso não encontrado: %s", context)
                raise LookupError(f"Recurso não encontrado: {context}")

            if response.status_code != 200:
                logger.error(
                    "Erro na requisição (%s). Status=%s Body=%s",
                    context,
                    response.status_code,
                    response.text,
                )
                raise EOLIntegrationError(
                    f"Erro na integração com EOL: {response.status_code}"
                )

            data = response.json()

            logger.info("Sucesso na requisição: %s", context)
            return data

        except requests.exceptions.Timeout:
            logger.error("Timeout: %s", context)
            raise EOLTimeoutError("Tempo limite excedido")

        except requests.exceptions.RequestException as e:
            logger.error("Erro de comunicação (%s): %s", context, str(e))
            raise EOLCommunicationError(str(e))


class DREIntegracaoService(BaseEOLService):
    @classmethod
    def get_dres(cls) -> list[dict]:
        base_url = env(ENV_URL, default="")
        url = f"{base_url}{ENDPOINT_DRES}"

        data = cls._get(url, "Listagem de DREs")

        if not isinstance(data, list):
            raise EOLUnexpectedResponseError(MSG_RESPOSTA_INVALIDA_LISTA)

        logger.info("DREs encontradas: %s", len(data))
        return data

    @classmethod
    def get_dre_by_codigo(cls, codigo_dre: str) -> dict | None:
        try:
            dres = cls.get_dres()

            for dre in dres:
                if dre.get("codigoDRE") == codigo_dre:
                    logger.info("DRE encontrada: %s", dre.get("nomeDRE"))
                    return dre

            logger.warning("DRE não encontrada com código: %s", codigo_dre)
            return None

        except PermissionError:
            logger.error("Erro ao buscar DRE por código: %s", codigo_dre)
            raise

        except EOLIntegrationError:
            logger.error("Erro ao buscar DRE por código: %s", codigo_dre)
            raise


class UnidadeIntegracaoService(BaseEOLService):
    DEFAULT_TIMEOUT = 50

    @classmethod
    def get_unidades_by_dre(cls, dre_codigo: str | int) -> list[dict]:
        dre_codigo_str = str(dre_codigo or "").strip()

        if not dre_codigo_str:
            logger.warning("dre_codigo não informado ou inválido")
            raise ValueError(MSG_DRE_OBRIGATORIO)

        base_url = env(ENV_URL, default="")
        url = f"{base_url}{ENDPOINT_UNIDADES.format(dre_codigo_str)}"

        data = cls._get(url, f"UEs da DRE {dre_codigo_str}")

        if not isinstance(data, list):
            raise EOLUnexpectedResponseError(MSG_RESPOSTA_INVALIDA_LISTA)

        logger.info("UEs encontradas: %s", len(data))
        return data

    @classmethod
    def get_unidades_by_dre_com_tipo_unidade(cls, dre_codigo: str | int) -> list[dict]:
        dre_codigo_str = str(dre_codigo or "").strip()

        if not dre_codigo_str:
            logger.warning(MSG_DRE_INVALIDO)
            raise ValueError(MSG_DRE_OBRIGATORIO)

        base_url = env(ENV_URL, default="")
        url = f"{base_url}{ENDPOINT_ESCOLAS.format(dre_codigo_str)}"

        data = cls._get(url, f"Escolas da DRE {dre_codigo_str}")

        if not isinstance(data, list):
            raise EOLUnexpectedResponseError(MSG_RESPOSTA_INVALIDA_LISTA)

        logger.info("Escolas encontradas: %s", len(data))
        return data

    @classmethod
    def get_unidades_codigo_integracao_by_dre(cls, dre_codigo: str | int) -> list[dict]:
        dre_codigo_str = str(dre_codigo or "").strip()

        if not dre_codigo_str:
            logger.warning(MSG_DRE_INVALIDO)
            raise ValueError(MSG_DRE_OBRIGATORIO)

        base_url = env(ENV_URL, default="")
        url = f"{base_url}{ENDPOINT_CODIGO_INTEGRACAO.format(dre_codigo_str)}"

        data = cls._get(url, f"Códigos integração da DRE {dre_codigo_str}")

        if not isinstance(data, list):
            raise EOLUnexpectedResponseError(MSG_RESPOSTA_INVALIDA_LISTA)

        logger.info("Códigos encontrados: %s", len(data))
        return data

    @classmethod
    def get_unidade_supervisao_by_dre(cls, dre_codigo: str | int) -> dict:
        dre_codigo_str = str(dre_codigo or "").strip()

        if not dre_codigo_str:
            logger.warning(MSG_DRE_INVALIDO)
            raise ValueError(MSG_DRE_OBRIGATORIO)

        codigo_escola_eol = SUPERVISAO_ESCOLAR_DRES_MAP.get(dre_codigo_str)

        if not codigo_escola_eol:
            logger.warning(
                "codigo_escola_eol não encontrado para a DRE '%s'",
                dre_codigo_str
            )
            raise ValueError(
                "DRE não possui unidade de supervisão configurada."
            )

        base_url = env(ENV_URL, default="")
        url = f"{base_url}/escolas/dados/{codigo_escola_eol}"

        data = cls._get(url, f"Unidade de supervisão da DRE {dre_codigo_str}")

        if not isinstance(data, dict):
            raise EOLUnexpectedResponseError(
                "Resposta inesperada da API (esperado um objeto)."
            )

        logger.info(
            "Unidade de supervisão encontrada para DRE '%s'",
            dre_codigo_str
        )

        return cls._formatar_unidade_supervisao(data)


    @staticmethod
    def _formatar_unidade_supervisao(data: dict) -> dict:
        return {
            "codigoEscola": data.get("codigo"),
            "nomeEscola": data.get("nome"),
            "codigoDRE": data.get("codigoDRE"),
            "tipoEscola": data.get("tipoUnidade"),
            "siglaTipoEscola": "UA",
            "nomeDRE": data.get("nomeDRE"),
            "siglaDRE": data.get("siglaDRE"),
            "codigoSubprefeitura": None,
            "nomeSubprefeitura": None,
        }
