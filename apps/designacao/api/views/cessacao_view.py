"""Views para a API de cessação.

Fornece endpoints para listagem, recuperação, criação e exclusão de cessões.
"""

from typing import Any

from django.db.models import QuerySet
from rest_framework import mixins, status, viewsets
from rest_framework.decorators import action
from rest_framework.pagination import PageNumberPagination
from rest_framework.request import Request
from rest_framework.response import Response

from apps.designacao.api.serializers.cessacao_serializer import (
    CessacaoReadSerializer,
    CessacaoReadSerializerById,
    CessacaoWriteSerializer,
)
from apps.designacao.api.views.designacao_base import (
    buscar_ato_por_portaria_ano,
)
from apps.designacao.services.cessacao_service import CessacaoService


class CessacaoPagination(PageNumberPagination):
    """Paginação padrão da API de cessações.

    Define paginação baseada em número de página com tamanho padrão
    de 10 registros por página, permitindo customização via parâmetro
    `page_size` limitado ao máximo de 100 itens.
    """

    page_size = 10
    page_size_query_param = "page_size"
    max_page_size = 100


class CessacaoViewSet(
    mixins.ListModelMixin,
    mixins.RetrieveModelMixin,
    mixins.DestroyModelMixin,
    viewsets.GenericViewSet,
):
    """ViewSet de cessação.

    Expõe operações de listagem, recuperação, criação e exclusão de cessões.
    """

    serializer_class = CessacaoReadSerializer
    pagination_class = CessacaoPagination

    def get_serializer_class(
        self,
    ) -> type[CessacaoReadSerializerById] | type[CessacaoReadSerializer]:
        """Retorna o serializer de cessacões para a view baseada no action.

        Returns:
            Serializer: Serializer de cessação.

        """
        if self.action == "retrieve":
            return CessacaoReadSerializerById
        return CessacaoReadSerializer

    def get_queryset(self) -> QuerySet:
        """Retorna o queryset de cessões para a view.

        Returns:
            QuerySet: Cessões ordenadas por data de criação decrescente.

        """
        return CessacaoService.listar()

    def create(self, request: Request, *args: Any, **kwargs: Any) -> Response:
        """Cria uma nova cessação com os dados recebidos.

        Args:
            request: Requisição HTTP contendo os dados de criação.
            *args: Argumentos posicionais adicionais.
            **kwargs: Argumentos nomeados adicionais.

        Returns:
            Response: Resposta HTTP com os dados da cessação criada.

        """
        serializer = CessacaoWriteSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.validated_data["criado_por"] = request.user

        ato = CessacaoService.criar(serializer.validated_data)

        return Response(
            CessacaoReadSerializer(CessacaoService.buscar(ato.pk)).data,
            status=status.HTTP_201_CREATED,
        )

    @action(detail=False, methods=["get"], url_path="buscar-por-portaria")
    def buscar_por_portaria(self, request: Request) -> Response:
        """Busca uma cessação pelo número da portaria e ano.

        Args:
            request: Requisição HTTP contendo os parâmetros `portaria` e
            `ano`.

        Returns:
            Response: Cessação encontrada ou erro 404/400.

        """
        ato, erro = buscar_ato_por_portaria_ano(
            request, self.get_queryset(), entidade="Cessação"
        )
        if erro is not None:
            return erro

        return Response(CessacaoReadSerializer(ato).data)
