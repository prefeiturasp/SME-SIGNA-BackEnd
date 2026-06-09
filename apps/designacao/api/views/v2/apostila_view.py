"""Views v2 para a API de apostilas.

Fornece endpoints para listagem, recuperação, criação e exclusão de apostilas.
"""

from django.db.models import QuerySet
from rest_framework import mixins, status, viewsets
from rest_framework.pagination import PageNumberPagination
from rest_framework.request import Request
from rest_framework.response import Response

from apps.designacao.api.serializers.v2.apostila_serializer import (
    ApostilaV2ReadSerializer,
    ApostilaV2WriteSerializer,
)
from apps.designacao.models.ato_administrativo import AtoAdministrativo
from apps.designacao.services.apostila_service import ApostilaService


class ApostilaV2Pagination(PageNumberPagination):
    """Paginação padrão da API V2 de apostilas.

    Define paginação baseada em número de página com tamanho padrão
    de 10 registros por página, permitindo customização via parâmetro
    `page_size` limitado ao máximo de 100 itens.
    """

    page_size = 10
    page_size_query_param = "page_size"
    max_page_size = 100


class ApostilaV2ViewSet(
    mixins.ListModelMixin,
    mixins.RetrieveModelMixin,
    mixins.DestroyModelMixin,
    viewsets.GenericViewSet,
):
    """ViewSet de apostilas v2.

    Expõe operações de listagem, recuperação, criação e exclusão de apostilas.
    """

    serializer_class = ApostilaV2ReadSerializer
    pagination_class = ApostilaV2Pagination

    def get_queryset(self) -> QuerySet:
        """Retorna o queryset de apostilas para a view.

        Returns:
            QuerySet: Apostilas ordenadas por data de criação decrescente.
        """
        return (
            AtoAdministrativo.objects.filter(
                tipo=AtoAdministrativo.Tipo.APOSTILA
            )
            .select_related("apostila_detalhe")
            .prefetch_related(
                "apostila_detalhe__alteracoes",
                "filhos",
                "filhos__insubsistencia_detalhe",
            )
            .order_by("-criado_em")
        )

    def create(self, request: Request, *args, **kwargs) -> Response:
        """Cria uma nova apostila a partir dos dados enviados na requisição.

        Args:
            request: Requisição HTTP contendo os dados de criação.
            *args: Argumentos posicionais adicionais.
            **kwargs: Argumentos nomeados adicionais.

        Returns:
            Response: Resposta HTTP com os dados da apostila criada.
        """
        serializer = ApostilaV2WriteSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        ato = ApostilaService.criar(serializer.validated_data)

        ato_com_prefetch = self.get_queryset().filter(pk=ato.pk).first()
        return Response(
            ApostilaV2ReadSerializer(ato_com_prefetch).data,
            status=status.HTTP_201_CREATED,
        )
