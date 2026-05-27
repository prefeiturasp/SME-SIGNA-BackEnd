"""Views v2 para a API de cessação.

Fornece endpoints para listagem, recuperação, criação e exclusão de cessões.
"""

from rest_framework import mixins, status, viewsets
from rest_framework.pagination import PageNumberPagination
from rest_framework.response import Response

from apps.designacao.api.serializers.v2.cessacao_serializer import (
    CessacaoV2ReadSerializer,
    CessacaoV2WriteSerializer,
)
from apps.designacao.models.ato_administrativo import AtoAdministrativo
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

    def get_queryset(self):
        """Retorna o queryset de cessões para a view.

        Returns:
            QuerySet: Cessões ordenadas por data de criação decrescente.
        """
        return (
            AtoAdministrativo.objects.filter(tipo=AtoAdministrativo.Tipo.CESSACAO)
            .select_related("cessacao_detalhe")
            .order_by("-criado_em")
        )

    def create(self, request, *args, **kwargs):
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

        ato = CessacaoService.criar(serializer.validated_data)

        ato_criado = self.get_queryset().filter(pk=ato.pk).first()
        return Response(
            CessacaoV2ReadSerializer(ato_criado).data,
            status=status.HTTP_201_CREATED,
        )
