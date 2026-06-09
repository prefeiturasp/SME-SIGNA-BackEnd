"""Views v2 para a API de insubsistência.

Fornece endpoints para listagem, recuperação, criação e exclusão de
insubsistências.
"""

from django.db.models import QuerySet
from rest_framework import mixins, status, viewsets
from rest_framework.pagination import PageNumberPagination
from rest_framework.request import Request
from rest_framework.response import Response

from apps.designacao.api.serializers.v2.insubsistencia_serializer import (
    InsubsistenciaV2ReadSerializer,
    InsubsistenciaV2WriteSerializer,
)
from apps.designacao.models.ato_administrativo import AtoAdministrativo
from apps.designacao.services.insubsistencia_service import (
    InsubsistenciaService,
)


class InsubsistenciaV2Pagination(PageNumberPagination):
    """Paginação padrão da API V2 de insubsistências.

    Define paginação baseada em número de página com tamanho padrão
    de 10 registros por página, permitindo customização via parâmetro
    `page_size` limitado ao máximo de 100 itens.
    """

    page_size = 10
    page_size_query_param = "page_size"
    max_page_size = 100


class InsubsistenciaV2ViewSet(
    mixins.ListModelMixin,
    mixins.RetrieveModelMixin,
    mixins.DestroyModelMixin,
    viewsets.GenericViewSet,
):
    """ViewSet de insubsistência v2.

    Expõe operações de listagem, recuperação, criação e exclusão de
    insubsistências.
    """

    serializer_class = InsubsistenciaV2ReadSerializer
    pagination_class = InsubsistenciaV2Pagination

    def get_queryset(self) -> QuerySet:
        """Retorna o queryset de insubsistências para a view.

        Returns:
            QuerySet: Insubsistências ordenadas por data de criação
            decrescente.
        """
        return (
            AtoAdministrativo.objects.filter(
                tipo=AtoAdministrativo.Tipo.INSUBSISTENCIA
            )
            .select_related("insubsistencia_detalhe")
            .order_by("-criado_em")
        )

    def create(self, request: Request, *args, **kwargs) -> Response:
        """Cria uma nova insubsistência a partir dos dados enviados.

        Args:
            request: Requisição HTTP contendo os dados de criação.
            *args: Argumentos posicionais adicionais.
            **kwargs: Argumentos nomeados adicionais.

        Returns:
            Response: Resposta HTTP com os dados da insubsistência criada.
        """
        serializer = InsubsistenciaV2WriteSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        ato = InsubsistenciaService.criar(serializer.validated_data)

        ato_criado = self.get_queryset().filter(pk=ato.pk).first()
        return Response(
            InsubsistenciaV2ReadSerializer(ato_criado).data,
            status=status.HTTP_201_CREATED,
        )

    def destroy(self, request: Request, *args, **kwargs) -> Response:
        """Remove a insubsistência e reactiva o ato pai associado.

        Args:
            request: Requisição HTTP de exclusão.
            *args: Argumentos posicionais adicionais.
            **kwargs: Argumentos nomeados adicionais.

        Returns:
            Response: Resposta HTTP vazia com status 204.
        """
        instancia = self.get_object()
        ato_pai = instancia.ato_pai
        if ato_pai:
            ato_pai.ativo = True
            ato_pai.save(update_fields=["ativo"])
        instancia.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)
