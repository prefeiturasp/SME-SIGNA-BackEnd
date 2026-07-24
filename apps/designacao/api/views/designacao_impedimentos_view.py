"""View para listagem de impedimentos de substituição.

Fornece endpoint para retorno de valores e labels de impedimentos usados na UI.
"""

from drf_spectacular.utils import extend_schema, inline_serializer
from rest_framework import serializers
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.designacao.models import ImpedimentoSubstituicao


class ImpedimentoSubstituicaoView(APIView):
    """View que retorna lista de impedimentos de substituição."""

    @extend_schema(
        responses=inline_serializer(
            "ImpedimentoSubstituicaoResponse",
            fields={
                "value": serializers.IntegerField(),
                "label": serializers.CharField(),
            },
            many=True,
        )
    )
    def get(self, request: Request) -> Response:
        """Recupera todos os impedimentos de substituição.

        Args:
            request: Requisição HTTP GET.

        Returns:
            Response: Lista de impedimentos com value/label.

        """
        impedimentos = ImpedimentoSubstituicao.objects.all()

        data = [{"value": i.id, "label": i.descricao} for i in impedimentos]

        return Response(data)
