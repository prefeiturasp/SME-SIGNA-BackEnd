from rest_framework import mixins, viewsets, status
from rest_framework.pagination import PageNumberPagination
from rest_framework.response import Response

from apps.designacao.models.ato_administrativo import AtoAdministrativo
from apps.designacao.api.serializers.v2.insubsistencia_serializer import (
    InsubsistenciaV2ReadSerializer,
    InsubsistenciaV2WriteSerializer,
)
from apps.designacao.services.insubsistencia_service import InsubsistenciaService


class InsubsistenciaV2Pagination(PageNumberPagination):
    page_size = 10
    page_size_query_param = 'page_size'
    max_page_size = 100


class InsubsistenciaV2ViewSet(
    mixins.ListModelMixin,
    mixins.RetrieveModelMixin,
    mixins.DestroyModelMixin,
    viewsets.GenericViewSet,
):
    serializer_class = InsubsistenciaV2ReadSerializer
    pagination_class = InsubsistenciaV2Pagination

    def get_queryset(self):
        return (
            AtoAdministrativo.objects
            .filter(tipo=AtoAdministrativo.Tipo.INSUBSISTENCIA)
            .select_related('insubsistencia_detalhe')
            .order_by('-criado_em')
        )

    def create(self, request, *args, **kwargs):
        serializer = InsubsistenciaV2WriteSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        ato = InsubsistenciaService.criar(serializer.validated_data)

        ato_criado = self.get_queryset().filter(pk=ato.pk).first()
        return Response(
            InsubsistenciaV2ReadSerializer(ato_criado).data,
            status=status.HTTP_201_CREATED,
        )

    def destroy(self, request, *args, **kwargs):
        instancia = self.get_object()
        ato_pai = instancia.ato_pai
        if ato_pai:
            ato_pai.ativo = True
            ato_pai.save(update_fields=['ativo'])
        instancia.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)
