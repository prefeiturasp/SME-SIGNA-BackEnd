"""View de pré-visualização do texto SEI.

Recebe o tipo de ato e os dados já preenchidos no formulário, resolve
o modelo de portaria vigente e retorna o texto pronto para exibição —
sem persistir nada.
"""

from rest_framework import permissions, status
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.designacao.api.serializers.texto_sei_serializer import (
    TextoSeiPreviewRequestSerializer,
    TextoSeiPreviewResponseSerializer,
)
from apps.designacao.services.texto_sei_service import TextoSeiService


class TextoSeiPreviewView(APIView):
    """View que gera a prévia do texto SEI de um ato."""

    permission_classes = [permissions.IsAuthenticated]

    def post(self, request: Request) -> Response:
        """Gera o texto SEI a partir do modelo de portaria vigente.

        Args:
            request: Requisição HTTP com `tipo_portaria`,
                `tipo_ato_pai` (quando aplicável), `tipo_cargo` e
                `dados`.

        Returns:
            Response: Modelo usado e texto gerado.

        """
        request_serializer = TextoSeiPreviewRequestSerializer(
            data=request.data
        )
        request_serializer.is_valid(raise_exception=True)
        validated = request_serializer.validated_data

        modelo, texto = TextoSeiService.gerar_preview(
            tipo_portaria=validated["tipo_portaria"],
            tipo_ato_pai=validated["tipo_ato_pai"],
            tipo_cargo=validated["tipo_cargo"],
            dados=validated["dados"],
        )

        response_serializer = TextoSeiPreviewResponseSerializer(
            {"modelo_portaria_id": modelo.pk, "texto": texto}
        )
        return Response(response_serializer.data, status=status.HTTP_200_OK)
