"""Views de infraestrutura do app core."""

from drf_spectacular.utils import extend_schema
from rest_framework.permissions import AllowAny
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView


class HealthView(APIView):
    """Verifica se a aplicação está no ar."""

    authentication_classes = []
    permission_classes = [AllowAny]

    @extend_schema(
        tags=["health"],
        summary="Liveness check",
        responses={
            200: {
                "type": "object",
                "properties": {"status": {"type": "string"}},
            }
        },
    )
    def get(self, request: Request) -> Response:
        """Retorna status ok se a aplicação estiver disponível."""
        return Response({"status": "ok"})
