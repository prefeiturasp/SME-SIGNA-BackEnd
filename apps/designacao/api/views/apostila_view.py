"""Views para a API de apostilas.

Fornece endpoints para criar, listar e recuperar apostilas.
"""

from typing import Any

from django.db.models import QuerySet
from rest_framework import mixins, status, viewsets
from rest_framework.exceptions import ValidationError
from rest_framework.request import Request
from rest_framework.response import Response

from apps.designacao.api.serializers.apostila_serializer import (
    ApostilaSerializer,
)
from apps.designacao.services.apostila_service import ApostilaService


class ApostilaViewSet(
    mixins.CreateModelMixin,
    mixins.ListModelMixin,
    mixins.RetrieveModelMixin,
    viewsets.GenericViewSet,
):
    """ViewSet de apostila.

    Permite criar novas apostilas, listar apostilas existentes e recuperar
    detalhes de uma apostila específica.
    """

    serializer_class = ApostilaSerializer

    def get_queryset(self) -> QuerySet:
        """Retorna o queryset de apostilas ativas.

        Returns:
            QuerySet: Apostilas não deletadas ordenadas por data de criação.

        """
        return ApostilaService.listar()

    def create(self, request: Request, *args: Any, **kwargs: Any) -> Response:
        """Cria uma nova apostila a partir dos dados da requisição.

        Args:
            request: Requisição HTTP contendo os dados da apostila.
            *args: Argumentos posicionais adicionais.
            **kwargs: Argumentos nomeados adicionais.

        Returns:
            Response: Resposta HTTP com os dados da apostila criada ou
            erro de validação.

        """
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        try:
            apostila = ApostilaService.criar_apostila(
                serializer.validated_data
            )

        except ValidationError as e:
            detail = e.detail
            message: str
            if isinstance(detail, list):
                message = str(detail[0])
            elif isinstance(detail, dict):
                first = next(iter(detail.values()))
                if isinstance(first, list):
                    message = str(first[0])
                else:
                    message = str(first)
            else:
                message = str(detail)

            return Response(
                {"detail": message}, status=status.HTTP_400_BAD_REQUEST
            )

        return Response(
            ApostilaSerializer(apostila).data, status=status.HTTP_201_CREATED
        )
