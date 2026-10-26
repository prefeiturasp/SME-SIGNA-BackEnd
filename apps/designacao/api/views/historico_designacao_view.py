"""View do histórico de designações de uma unidade escolar.

Retorna todas as designações de uma UE com a situação de vigência, a
data de cessação (quando houver cessação válida) e a árvore de atos
relacionados.
"""

from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import (
    OpenApiParameter,
    OpenApiResponse,
    extend_schema,
)
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.designacao.api.serializers.historico_designacao_serializer import (
    HistoricoDesignacaoSerializer,
)
from apps.designacao.services.historico_designacao_service import (
    HistoricoDesignacaoService,
)


class HistoricoDesignacaoView(APIView):
    """View que retorna o histórico de designações de uma unidade escolar."""

    permission_classes = [IsAuthenticated]

    @extend_schema(
        parameters=[
            OpenApiParameter(
                name="codigo_ue",
                type=OpenApiTypes.STR,
                location=OpenApiParameter.PATH,
                required=True,
                description="Código EOL da unidade escolar.",
            ),
        ],
        responses={
            200: OpenApiResponse(
                response=HistoricoDesignacaoSerializer(many=True),
                description=(
                    "Designações da UE com portaria, cargo, servidor "
                    "indicado, data da designação, vigência, data de "
                    "cessação e uma lista plana com todos os atos "
                    "relacionados."
                ),
            ),
        },
    )
    def get(self, request: Request, codigo_ue: str) -> Response:
        """Retorna as designações da unidade escolar informada.

        Unidade sem designações devolve lista vazia (e não 404), pois a
        tela de histórico precisa exibir o estado vazio.

        Args:
            request: Requisição HTTP.
            codigo_ue: Código EOL da unidade escolar (obrigatório na URL).

        Returns:
            Response: Lista de designações com os atos relacionados.

        """
        designacoes = HistoricoDesignacaoService.listar_por_ue(codigo_ue)
        return Response(
            HistoricoDesignacaoSerializer(designacoes, many=True).data,
            status=status.HTTP_200_OK,
        )
