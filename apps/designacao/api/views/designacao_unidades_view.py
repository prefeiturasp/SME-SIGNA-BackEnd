"""Views para informações de unidades relacionadas à designação.

Inclui endpoints para obter dados escolares de unidade e listar cargos
disponíveis.
"""

import logging

from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import (
    OpenApiParameter,
    OpenApiResponse,
    extend_schema,
    inline_serializer,
)
from rest_framework import serializers, status
from rest_framework.permissions import IsAuthenticated
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.designacao.services.designacao_unidades_service import (
    DesignacaoUnidadeService,
)
from apps.helpers.exceptions import SmeIntegracaoError

logger = logging.getLogger(__name__)


class DesignacaoUnidadeView(APIView):
    """View que retorna informações escolares de uma unidade."""

    permission_classes = [IsAuthenticated]

    @extend_schema(
        parameters=[
            OpenApiParameter(
                name="codigo_ue",
                type=OpenApiTypes.STR,
                location=OpenApiParameter.QUERY,
                required=True,
                description="Código EOL da unidade escolar.",
            ),
        ],
        responses={
            200: OpenApiResponse(
                response=OpenApiTypes.OBJECT,
                description="Dados escolares da unidade (integração SME).",
            ),
            400: inline_serializer(
                "DesignacaoUnidadeErroResponse",
                fields={"detail": serializers.CharField()},
            ),
            500: inline_serializer(
                "DesignacaoUnidadeErroInternoResponse",
                fields={"detail": serializers.CharField()},
            ),
        },
    )
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

        except SmeIntegracaoError as e:
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

    @extend_schema(
        responses={
            200: OpenApiResponse(
                response=OpenApiTypes.OBJECT,
                description="Lista de cargos de vaga disponíveis.",
            ),
            500: inline_serializer(
                "DesignacaoUnidadeCargosErroResponse",
                fields={"detail": serializers.CharField()},
            ),
        },
    )
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
