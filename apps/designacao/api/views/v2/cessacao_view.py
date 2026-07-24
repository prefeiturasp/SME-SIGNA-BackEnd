"""Views v2 para a API de cessação.

Fornece endpoints para listagem, recuperação, criação e exclusão de cessões.
"""

from typing import Any

from django.db.models import QuerySet
from rest_framework import mixins, status, viewsets
from rest_framework.decorators import action
from rest_framework.pagination import PageNumberPagination
from rest_framework.request import Request
from rest_framework.response import Response

from apps.designacao.api.serializers.v2.cessacao_serializer import (
    CessacaoV2ReadSerializer,
    CessacaoV2WriteSerializer,
)
from apps.designacao.services.cessacao_service import CessacaoService


class CessacaoV2Pagination(PageNumberPagination):
    """Paginação padrão da API V2 de cessações.

    Define paginação baseada em número de página com tamanho padrão
    de 10 registros por página, permitindo customização via parâmetro
    `page_size` limitado ao máximo de 100 itens.
    """

    page_size = 10
    page_size_query_param = "page_size"
    max_page_size = 100


class CessacaoV2ViewSet(
    mixins.ListModelMixin,
    mixins.RetrieveModelMixin,
    mixins.DestroyModelMixin,
    viewsets.GenericViewSet,
):
    """ViewSet de cessação v2.

    Expõe operações de listagem, recuperação, criação e exclusão de cessões.
    """

    serializer_class = CessacaoV2ReadSerializer
    pagination_class = CessacaoV2Pagination

    def get_queryset(self) -> QuerySet:
        """Retorna o queryset de cessões para a view.

        Returns:
            QuerySet: Cessões ordenadas por data de criação decrescente.

        """
        return CessacaoService.listar_v2()

    def create(self, request: Request, *args: Any, **kwargs: Any) -> Response:
        """Cria uma nova cessação com os dados recebidos.

        Args:
            request: Requisição HTTP contendo os dados de criação.
            *args: Argumentos posicionais adicionais.
            **kwargs: Argumentos nomeados adicionais.

        Returns:
            Response: Resposta HTTP com os dados da cessação criada.

        """
        serializer = CessacaoV2WriteSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.validated_data["criado_por"] = request.user

        ato = CessacaoService.criar(serializer.validated_data)

        return Response(
            CessacaoV2ReadSerializer(CessacaoService.buscar_v2(ato.pk)).data,
            status=status.HTTP_201_CREATED,
        )

    @action(detail=False, methods=["get"], url_path="buscar-por-portaria")
    def buscar_por_portaria(self, request: Request) -> Response:
        """Busca uma cessação pelo número da portaria.

        Args:
            request: Requisição HTTP contendo o parâmetro `portaria`.

        Returns:
            Response: Cessação encontrada ou erro 404/400.

        """
        portaria = (request.query_params.get("portaria") or "").strip()
        if not portaria:
            return Response(
                {"detail": "Parâmetro 'portaria' é obrigatório."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        ato = self.get_queryset().filter(numero_portaria=portaria).first()
        if ato is None:
            return Response(
                {"detail": "Cessação não encontrada para essa portaria."},
                status=status.HTTP_404_NOT_FOUND,
            )

        return Response(CessacaoV2ReadSerializer(ato).data)
