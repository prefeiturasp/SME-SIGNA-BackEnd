import logging

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status, permissions
from rest_framework.exceptions import ValidationError

from apps.designacao.api.serializers.designacao_servidor_request_serializer import (
    DesignacaoServidorRequestSerializer
)
from apps.designacao.services.designacao_servidor_service import (
    DesignacaoServidorService
)
from apps.helpers.exceptions import SmeIntegracaoException

logger = logging.getLogger(__name__)


class DesignacaoServidorView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        serializer = DesignacaoServidorRequestSerializer(
            data=request.data
        )

        try:
            serializer.is_valid(raise_exception=True)
        except ValidationError:
            return Response(
                {"detail": "RF inválido"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        rf = serializer.validated_data["rf"]

        try:
            dados = DesignacaoServidorService.obter_designacao(rf)

            return Response(
                dados,
                status=status.HTTP_200_OK
            )

        except SmeIntegracaoException as e:
            logger.warning(
                "Erro ao obter designação do servidor: %s",
                str(e)
            )
            return Response(
                {"detail": str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )

        except Exception as e:
            logger.error(
                "Erro interno designação servidor: %s",
                e
            )
            return Response(
                {"detail": "Erro interno"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
