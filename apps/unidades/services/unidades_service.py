import logging
import requests
import environ
from typing import Dict, List, Optional
from django.conf import settings

env = environ.Env()
logger = logging.getLogger(__name__)


class DREIntegracaoService:
    """Serviço para busca de unidades no sistema EOL"""
    
    DEFAULT_HEADERS = {
        'Content-Type': 'application/json',
        'x-api-eol-key': env('SME_INTEGRACAO_TOKEN', default='')
    }
    DEFAULT_TIMEOUT = 30
    
    @classmethod
    def get_dres(cls) -> list[dict]:
        """Busca todas as DREs do sistema EOL"""
        
        url = f"{env('SME_INTEGRACAO_URL', default='')}/api/DREs"
        
        try:
            logger.info("Buscando DREs no EOL")
            
            response = requests.get(
                url,
                headers=cls.DEFAULT_HEADERS,
                timeout=cls.DEFAULT_TIMEOUT
            )
            
            if response.status_code == 401:
                logger.error("Não autorizado ao buscar DREs no EOL")
                raise PermissionError("Não autorizado a acessar o sistema EOL")
            
            if response.status_code != 200:
                logger.error("Erro ao buscar DREs no EOL. Status: %s", response.status_code)
                raise Exception(f"Erro na consulta de DREs: {response.status_code}")
            
            dres_data = response.json()
            logger.info("DREs encontradas: %s", len(dres_data))
            
            return dres_data
            
        except requests.exceptions.Timeout:
            logger.error("Timeout ao buscar DREs no EOL")
            raise Exception("Tempo limite excedido ao consultar DREs")
        
        except requests.exceptions.RequestException as e:
            logger.error("Erro de comunicação com EOL: %s", str(e))
            raise Exception(f"Erro de comunicação com sistema de DREs: {str(e)}")
        
        except Exception as e:
            logger.error("Erro inesperado ao buscar DREs: %s", str(e))
            raise
    
    @classmethod
    def get_dre_by_codigo(cls, codigo_dre: str) -> dict | None:
        """Busca uma DRE específica pelo código"""
        
        try:
            dres = cls.get_dres()
            
            for dre in dres:
                if dre.get('codigoDRE') == codigo_dre:
                    logger.info("DRE encontrada: %s", dre.get('nomeDRE'))
                    return dre
            
            logger.warning("DRE não encontrada com código: %s", codigo_dre)
            return None
            
        except Exception as e:
            logger.error("Erro ao buscar DRE por código: %s", str(e))
            raise


class UnidadeIntegracaoService:
    """Serviço para busca de unidades no sistema EOL"""
    
    DEFAULT_HEADERS = {
        'Content-Type': 'application/json',
        'x-api-eol-key': env('SME_INTEGRACAO_TOKEN', default='')
    }
    DEFAULT_TIMEOUT = 50

    @classmethod
    def get_unidades_by_dre(cls, dre_codigo: str | int) -> list[dict]:
        """
        Busca todas as Unidades (UEs) de uma DRE pelo código da DRE.
        """
        # Normaliza: converte para string e remove espaços. Se for None, vira string vazia.
        dre_codigo_str = str(dre_codigo or "").strip()
        
        if not dre_codigo_str:
            logger.warning("dre_codigo não informado ou inválido para consulta de unidades")
            raise ValueError("É necessário informar o código da DRE (dre_codigo).")

        base_url = env("SME_INTEGRACAO_URL", default="")
        # Usa a versão limpa (string) na URL
        url = f"{base_url}/api/DREs/{dre_codigo_str}/unidades"

        try:
            logger.info("Buscando UEs da DRE '%s' no EOL", dre_codigo_str)

            response = requests.get(
                url,
                headers=cls.DEFAULT_HEADERS,
                timeout=cls.DEFAULT_TIMEOUT,
            )

            if response.status_code == 401:
                logger.error("Não autorizado ao buscar UEs da DRE '%s' no EOL", dre_codigo)
                raise PermissionError("Não autorizado a acessar o sistema EOL (verifique x-api-eol-key).")

            if response.status_code == 404:
                logger.warning("DRE não encontrada ao buscar UEs. dre_codigo='%s'", dre_codigo)
                raise LookupError(f"DRE não encontrada: {dre_codigo}")

            if response.status_code != 200:
                logger.error(
                    "Erro ao buscar UEs da DRE '%s'. Status=%s Body=%s",
                    dre_codigo, response.status_code, response.text
                )
                raise Exception(f"Erro na consulta de UEs por DRE: {response.status_code}")

            unidades_data = response.json()

            if not isinstance(unidades_data, list):
                logger.error(
                    "Resposta inesperada ao buscar UEs da DRE '%s'. Tipo=%s",
                    dre_codigo, type(unidades_data).__name__
                )
                raise Exception("Resposta inesperada da API ao consultar UEs por DRE (esperado uma lista).")

            logger.info("UEs encontradas para DRE '%s': %d", dre_codigo, len(unidades_data))
            return unidades_data

        except requests.exceptions.Timeout:
            logger.error("Timeout ao buscar UEs da DRE '%s' no EOL", dre_codigo)
            raise Exception("Tempo limite excedido ao consultar UEs por DRE.")

        except requests.exceptions.RequestException as e:
            logger.error("Erro de comunicação com EOL ao buscar UEs da DRE '%s': %s", dre_codigo, str(e))
            raise Exception(f"Erro de comunicação com sistema de unidades: {str(e)}")

        except Exception as e:
            logger.error("Erro inesperado ao buscar UEs da DRE '%s': %s", dre_codigo, str(e))
            raise
        