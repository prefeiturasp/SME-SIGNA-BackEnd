from rest_framework.response import Response
from rest_framework import mixins, viewsets, status
from rest_framework.pagination import PageNumberPagination

from apps.designacao.models.cessacao import Cessacao
from apps.designacao.api.serializers.cessacao_serializer import CessacaoSerializer

class CessacaoPagination(PageNumberPagination):
    page_size = 10
    page_size_query_param = 'page_size'
    max_page_size = 100

class CessacaoViewSet(
    mixins.CreateModelMixin,
    mixins.ListModelMixin,
    mixins.RetrieveModelMixin,
    mixins.DestroyModelMixin,
    viewsets.GenericViewSet
):
    serializer_class = CessacaoSerializer
    pagination_class = CessacaoPagination

    def get_queryset(self):
        return Cessacao.objects.filter(
            is_deleted=False
        ).select_related(
            'designacao'
        ).order_by('-criado_em')

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        instance.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)