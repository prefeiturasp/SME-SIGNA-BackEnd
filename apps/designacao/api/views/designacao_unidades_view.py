import logging

from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status

from apps.designacao.services.designacao_unidades_service import (
    DesignacaoUnidadeService
)
from apps.helpers.exceptions import SmeIntegracaoException

logger = logging.getLogger(__name__)

class DesignacaoUnidadeView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        codigo_ue = request.query_params.get("codigo_ue")

        if not codigo_ue:
            return Response(
                {"detail": "codigo_ue é obrigatório"},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            result = DesignacaoUnidadeService.obter_informacoes_escolares(
                codigo_ue
            )
            return Response(result, status=status.HTTP_200_OK)

        except SmeIntegracaoException as e:
            return Response(
                {"detail": str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )

        except Exception as e:
            logger.exception("Erro inesperado ao buscar designação da unidade")
            return Response(
                {"detail": "Erro interno do servidor"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


