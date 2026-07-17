"""Views para a API de insubsistência.

Fornece endpoints para listagem, recuperação, criação e exclusão de
insubsistências.
"""

from typing import Any

from django.db.models import QuerySet
from rest_framework import mixins, status, viewsets
from rest_framework.decorators import action
from rest_framework.pagination import PageNumberPagination
from rest_framework.request import Request
from rest_framework.response import Response

from apps.designacao.api.serializers.insubsistencia_serializer import (
    InsubsistenciaReadSerializer,
    InsubsistenciaWriteSerializer,
)
from apps.designacao.services.insubsistencia_service import (
    InsubsistenciaService,
)


class InsubsistenciaPagination(PageNumberPagination):
    """Paginação padrão da API de insubsistências.

    Define paginação baseada em número de página com tamanho padrão
    de 10 registros por página, permitindo customização via parâmetro
    `page_size` limitado ao máximo de 100 itens.
    """

    page_size = 10
    page_size_query_param = "page_size"
    max_page_size = 100


class InsubsistenciaViewSet(
    mixins.ListModelMixin,
    mixins.RetrieveModelMixin,
    mixins.DestroyModelMixin,
    viewsets.GenericViewSet,
):
    """ViewSet de insubsistência.

    Expõe operações de listagem, recuperação, criação e exclusão de
    insubsistências.
    """

    serializer_class = InsubsistenciaReadSerializer
    pagination_class = InsubsistenciaPagination

    def get_queryset(self) -> QuerySet:
        """Retorna o queryset de insubsistências para a view.

        Returns:
            QuerySet: Insubsistências ordenadas por data de criação
            decrescente.

        """
        return InsubsistenciaService.listar()

    def create(self, request: Request, *args: Any, **kwargs: Any) -> Response:
        """Cria uma nova insubsistência a partir dos dados enviados.

        Args:
            request: Requisição HTTP contendo os dados de criação.
            *args: Argumentos posicionais adicionais.
            **kwargs: Argumentos nomeados adicionais.

        Returns:
            Response: Resposta HTTP com os dados da insubsistência criada.

        """
        serializer = InsubsistenciaWriteSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.validated_data["criado_por"] = request.user

        ato = InsubsistenciaService.criar(serializer.validated_data)

        return Response(
            InsubsistenciaReadSerializer(
                InsubsistenciaService.buscar(ato.pk)
            ).data,
            status=status.HTTP_201_CREATED,
        )

    def destroy(self, request: Request, *args: Any, **kwargs: Any) -> Response:
        """Remove a insubsistência e reativa o ato pai associado.

        Args:
            request: Requisição HTTP de exclusão.
            *args: Argumentos posicionais adicionais.
            **kwargs: Argumentos nomeados adicionais.

        Returns:
            Response: Resposta HTTP vazia com status 204.

        """
        InsubsistenciaService.excluir(self.get_object())
        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(detail=False, methods=["get"], url_path="buscar-por-portaria")
    def buscar_por_portaria(self, request: Request) -> Response:
        """Busca uma insubsistência pelo número da portaria.

        Args:
            request: Requisição HTTP contendo o parâmetro `portaria`.

        Returns:
            Response: Insubsistência encontrada ou erro 404/400.

        """
        portaria = (request.query_params.get("portaria") or "").strip()
        if not portaria:
            return Response(
                {"detail": "Parâmetro 'portaria' é obrigatório."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        ato = self.get_queryset().filter(numero_portaria=portaria).first()
        if ato is None:
            detail = "Insubsistência não encontrada para essa portaria."
            return Response(
                {"detail": detail},
                status=status.HTTP_404_NOT_FOUND,
            )

        return Response(InsubsistenciaReadSerializer(ato).data)
