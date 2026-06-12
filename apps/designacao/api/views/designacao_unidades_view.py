"""Views para informações de unidades relacionadas à designação.

Inclui endpoints para obter dados escolares de unidade e listar cargos
disponíveis.
"""

import logging

from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.designacao.services.designacao_unidades_service import (
    DesignacaoUnidadeService,
)
from apps.helpers.exceptions import SmeIntegracaoException

logger = logging.getLogger(__name__)


class DesignacaoUnidadeView(APIView):
    """View que retorna informações escolares de uma unidade."""

    permission_classes = [IsAuthenticated]

    def get(self, request: Request) -> Response:
        """Recupera informações escolares da unidade especificada.

        Args:
            request: Requisição HTTP contendo o código_ue.

        Returns:
            Response: Dados escolares da unidade ou mensagem de erro.
        """
        codigo_ue = request.query_params.get("codigo_ue")

        if not codigo_ue:
            return Response(
                {"detail": "codigo_ue é obrigatório"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            result = DesignacaoUnidadeService.obter_informacoes_escolares(
                codigo_ue
            )
            return Response(result, status=status.HTTP_200_OK)

        except SmeIntegracaoException as e:
            return Response(
                {"detail": str(e)}, status=status.HTTP_400_BAD_REQUEST
            )

        except Exception:
            logger.exception("Erro inesperado ao buscar designação da unidade")
            return Response(
                {"detail": "Erro interno do servidor"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )


class DesignacaoUnidadeCargosView(APIView):
    """View que retorna cargos disponíveis de unidades."""

    permission_classes = [IsAuthenticated]

    def get(self, request: Request) -> Response:
        """Retorna a lista de cargos de vaga disponíveis.

        Args:
            request: Requisição HTTP GET.

        Returns:
            Response: Lista de cargos ou mensagem de erro.
        """
        try:
            cargos = DesignacaoUnidadeService.listar_cargos_vaga()
            return Response(cargos, status=status.HTTP_200_OK)
        except Exception:
            logger.exception("Erro ao buscar lista de cargos")
            return Response(
                {"detail": "Erro interno ao buscar cargos"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )
