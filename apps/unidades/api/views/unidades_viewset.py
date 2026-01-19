import logging
 
from rest_framework import status
from rest_framework.response import Response
from rest_framework.decorators import action
from rest_framework.viewsets import ViewSet
from rest_framework.permissions import AllowAny

from apps.unidades.services.unidades_service import UnidadeIntegracaoService, DREIntegracaoService
 
logger = logging.getLogger(__name__)
 
 
class UnidadeViewSet(ViewSet):
    """
    ViewSet para consulta de Unidades (DREs e UEs) via API SME Integração.
    Não utiliza banco de dados local, consome API externa.
    """
    permission_classes = [AllowAny]
 
    def list(self, request, *args, **kwargs):
        """
        Lista unidades conforme parâmetros:
        - tipo=DRE: lista todas as DREs
        - tipo=UE&dre={codigo}: lista UEs de uma DRE específica
        """
        tipo = request.query_params.get("tipo")
        codigo_dre = request.query_params.get("dre")
        
        logger.info(
            "Listagem de unidades solicitada com tipo='%s', dre='%s'",
            tipo, codigo_dre
        )
 
        if tipo == "DRE":
            return self._listar_dres()
 
        if tipo == "UE":
            return self._listar_ues(codigo_dre)
 
        if tipo is None:
            logger.warning("Nenhum parâmetro 'tipo' informado.")
            return self._resposta_erro(
                "É necessário informar o parâmetro 'tipo' (DRE ou UE).",
                status.HTTP_400_BAD_REQUEST
            )
 
        logger.warning("Parâmetro 'tipo' inválido recebido: %s", tipo)
        return self._resposta_erro(
            "Parâmetro 'tipo' inválido. Use 'DRE' ou 'UE'.",
            status.HTTP_400_BAD_REQUEST
        )
 
    def _listar_dres(self):
        """Lista todas as DREs da API SME Integração"""
        try:
            dres = DREIntegracaoService.get_dres()
            logger.info("DREs encontradas: %d", len(dres))
            return Response(dres)
            
        except PermissionError as e:
            logger.error("Erro de permissão ao buscar DREs: %s", str(e))
            return self._resposta_erro(str(e), status.HTTP_401_UNAUTHORIZED)
            
        except Exception as e:
            logger.error("Erro ao buscar DREs: %s", str(e))
            return self._resposta_erro(
                "Erro ao consultar DREs no sistema externo.",
                status.HTTP_500_INTERNAL_SERVER_ERROR
            )
 
    def _listar_ues(self, codigo_dre):
        """
        Lista Unidades Escolares vinculadas a uma DRE.
        
        Args:
            codigo_dre: Código EOL da DRE (ex: "108200")
        """
        if not codigo_dre:
            logger.warning("Parâmetro 'dre' não informado para tipo UE")
            return self._resposta_erro(
                "É necessário informar o código da DRE no parâmetro 'dre'.",
                status.HTTP_400_BAD_REQUEST
            )
 
        try:
            unidades = UnidadeIntegracaoService.get_unidades_by_dre(codigo_dre)
            logger.info("UEs encontradas para DRE '%s': %d", codigo_dre, len(unidades))
            return Response(unidades)
            
        except ValueError as e:
            logger.warning("Parâmetro inválido: %s", str(e))
            return self._resposta_erro(str(e), status.HTTP_400_BAD_REQUEST)
            
        except LookupError as e:
            logger.warning("DRE não encontrada: %s", codigo_dre)
            return self._resposta_erro(str(e), status.HTTP_404_NOT_FOUND)
            
        except PermissionError as e:
            logger.error("Erro de permissão ao buscar UEs: %s", str(e))
            return self._resposta_erro(str(e), status.HTTP_401_UNAUTHORIZED)
            
        except Exception as e:
            logger.error("Erro ao buscar UEs da DRE '%s': %s", codigo_dre, str(e))
            return self._resposta_erro(
                "Erro ao consultar unidades no sistema externo.",
                status.HTTP_500_INTERNAL_SERVER_ERROR
            )
 
    def _resposta_erro(self, mensagem, status_code):
        """Retorna resposta de erro padronizada"""
        return Response({"detail": mensagem}, status=status_code)
