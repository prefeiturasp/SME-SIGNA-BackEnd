"""Views para a API de regras de portaria.

Fornece endpoints para listagem, criação, consulta e edição de regras
de portaria cadastradas.
"""

from typing import Any

from django.db.models import QuerySet
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import mixins, status, viewsets
from rest_framework.pagination import PageNumberPagination
from rest_framework.request import Request
from rest_framework.response import Response

from apps.gestao.api.filters.regra_portaria_filter import RegraPortariaFilter
from apps.gestao.api.serializers.regra_portaria_serializer import (
    RegraPortariaReadSerializer,
    RegraPortariaUpdateSerializer,
    RegraPortariaWriteSerializer,
)
from apps.gestao.models.regra_portaria import RegraPortaria
from apps.gestao.services.regra_portaria_service import RegraPortariaService


class RegraPortariaPagination(PageNumberPagination):
    """Paginação padrão da API de regras de portaria.

    Define paginação baseada em número de página com tamanho padrão
    de 10 registros por página, permitindo customização via parâmetro
    `page_size` limitado ao máximo de 100 itens.
    """

    page_size = 10
    page_size_query_param = "page_size"
    max_page_size = 100


class RegraPortariaViewSet(
    mixins.ListModelMixin,
    mixins.RetrieveModelMixin,
    mixins.CreateModelMixin,
    viewsets.GenericViewSet,
):
    """ViewSet de regras de portaria.

    Expõe operações de listagem (com filtros e paginação), consulta
    individual, criação e edição de regras de portaria.
    """

    serializer_class = RegraPortariaReadSerializer
    pagination_class = RegraPortariaPagination
    filter_backends = [DjangoFilterBackend]
    filterset_class = RegraPortariaFilter

    def get_queryset(self) -> QuerySet[RegraPortaria]:
        """Retorna o queryset de regras de portaria para a view.

        Returns:
            QuerySet: Regras de portaria cadastradas.

        """
        return RegraPortariaService.listar()

    def create(self, request: Request, *args: Any, **kwargs: Any) -> Response:
        """Cria uma nova regra de portaria a partir dos dados enviados.

        Args:
            request: Requisição HTTP contendo os dados de criação.
            *args: Argumentos posicionais adicionais.
            **kwargs: Argumentos nomeados adicionais.

        Returns:
            Response: Resposta HTTP com os dados da regra de portaria criada.

        """
        serializer = RegraPortariaWriteSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        regra = RegraPortariaService.criar(serializer.validated_data)

        return Response(
            RegraPortariaReadSerializer(regra).data,
            status=status.HTTP_201_CREATED,
        )

    def partial_update(
        self, request: Request, *args: Any, **kwargs: Any
    ) -> Response:
        """Atualiza parcialmente uma regra de portaria existente.

        Args:
            request: Requisição HTTP contendo os campos a atualizar.
            *args: Argumentos posicionais adicionais.
            **kwargs: Argumentos nomeados adicionais.

        Returns:
            Response: Resposta HTTP com os dados atualizados da regra de
            portaria.

        """
        regra = self.get_object()
        serializer = RegraPortariaUpdateSerializer(
            regra, data=request.data, partial=True
        )
        serializer.is_valid(raise_exception=True)

        regra = RegraPortariaService.atualizar(
            regra, serializer.validated_data
        )

        return Response(RegraPortariaReadSerializer(regra).data)
