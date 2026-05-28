"""Views para a API de cessação.

Fornece endpoints para criar, listar, recuperar e excluir cessões.
"""

from rest_framework import mixins, viewsets
from rest_framework.pagination import PageNumberPagination

from apps.designacao.api.serializers.cessacao_serializer import (
    CessacaoSerializer,
)
from apps.designacao.models.cessacao import Cessacao


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
    mixins.CreateModelMixin,
    mixins.ListModelMixin,
    mixins.RetrieveModelMixin,
    mixins.DestroyModelMixin,
    viewsets.GenericViewSet,
):
    """ViewSet de cessação.

    Expõe operações básicas para o CRUD de cessões.
    """

    serializer_class = CessacaoSerializer
    pagination_class = CessacaoPagination

    def get_queryset(self):
        """Retorna o queryset de cessões ativas.

        Returns:
            QuerySet: Cessões não deletadas ordenadas por data de criação.
        """
        return (
            Cessacao.objects.filter(is_deleted=False)
            .select_related("designacao")
            .order_by("-criado_em")
        )
