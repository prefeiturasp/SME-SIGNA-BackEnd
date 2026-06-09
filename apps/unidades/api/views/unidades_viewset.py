"""Viewset para consulta de DREs e Unidades Escolares via API SME Integração.

Este módulo fornece endpoints que consomem serviços externos para listar DREs
ou UEs de uma DRE específica, sem usar banco de dados local.
"""

import logging

from rest_framework import status
from rest_framework.permissions import AllowAny
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.viewsets import ViewSet

from apps.unidades.services.unidades_service import (
    DREIntegracaoService,
    UnidadeIntegracaoService,
)

logger = logging.getLogger(__name__)


class UnidadeViewSet(ViewSet):
    """ViewSet para consulta de DREs e UEs via API SME Integração.

    O viewset encaminha requisições para os serviços de integração e trata as
    respostas e erros retornados pelos sistemas externos.
    """

    permission_classes = [AllowAny]

    def list(self, request: Request, *args, **kwargs) -> Response:
        """Lista DREs ou UEs conforme os parâmetros da requisição.

        Args:
            request (rest_framework.request.Request): Requisição HTTP recebida.
            *args: Argumentos posicionais adicionais.
            **kwargs: Argumentos nomeados adicionais.

        Returns:
            rest_framework.response.Response: A resposta com a lista de DREs ou
                unidades escolares, ou uma mensagem de erro.

        """
        tipo = request.query_params.get("tipo")
        codigo_dre = request.query_params.get("dre")

        logger.info(
            "Listagem de unidades solicitada com tipo='%s', dre='%s'",
            tipo,
            codigo_dre,
        )

        if tipo == "DRE":
            return self._listar_dres()

        if tipo == "UE":

            return self._listar_ues(codigo_dre)

        if tipo is None:
            logger.warning("Nenhum parâmetro 'tipo' informado.")
            return self._resposta_erro(
                "É necessário informar o parâmetro 'tipo' (DRE ou UE).",
                status.HTTP_400_BAD_REQUEST,
            )

        logger.warning("Parâmetro 'tipo' inválido recebido: %s", tipo)
        return self._resposta_erro(
            "Parâmetro 'tipo' inválido. Use 'DRE' ou 'UE'.",
            status.HTTP_400_BAD_REQUEST,
        )

    def _listar_dres(self) -> Response:
        """Recupera todas as DREs a partir da API SME Integração.

        Returns:
            rest_framework.response.Response: Resposta com a lista de DREs ou
                mensagem de erro em caso de falha.

        """
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
                status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

    def _listar_ues(self, codigo_dre: str | None) -> Response:
        """Recupera as Unidades Escolares vinculadas a uma DRE específica.

        Args:
            codigo_dre (str): Código EOL da DRE (por exemplo, "108200").

        Returns:
            rest_framework.response.Response: Resposta com a lista de unidades
                ou mensagem de erro em caso de falha.

        """
        if not codigo_dre:
            logger.warning("Parâmetro 'dre' não informado para tipo UE")
            return self._resposta_erro(
                "É necessário informar o código da DRE no parâmetro 'dre'.",
                status.HTTP_400_BAD_REQUEST,
            )

        unidade_supervisao = None
        try:
            unidade_supervisao = (
                UnidadeIntegracaoService.get_unidade_supervisao_by_dre(
                    codigo_dre
                )
            )
            logger.info(
                "Unidades de supervisão encontradas para DRE '%s'", codigo_dre
            )
        except Exception as e:
            logger.error(
                "Erro ao buscar Unidade de supervisão da DRE '%s': %s",
                codigo_dre,
                str(e),
            )

        try:

            unidades = (
                UnidadeIntegracaoService.get_unidades_by_dre_com_tipo_unidade(
                    codigo_dre
                )
            )

            logger.info(
                "UEs encontradas para DRE '%s': %d", codigo_dre, len(unidades)
            )

            if unidade_supervisao:
                unidades.append(unidade_supervisao)

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
            logger.error(
                "Erro ao buscar UEs da DRE '%s': %s", codigo_dre, str(e)
            )
            return self._resposta_erro(
                "Erro ao consultar unidades no sistema externo.",
                status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

    def _resposta_erro(self, mensagem: str, status_code: int) -> Response:
        """Retorna uma resposta de erro padronizada.

        Args:
            mensagem (str): Mensagem de erro a ser retornada.
            status_code (int): Código HTTP do erro.

        Returns:
            rest_framework.response.Response: A resposta de erro formatada.

        """
        return Response({"detail": mensagem}, status=status_code)
