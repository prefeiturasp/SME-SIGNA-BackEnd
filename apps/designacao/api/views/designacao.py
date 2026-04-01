from rest_framework import mixins, viewsets, filters, status
from rest_framework.pagination import PageNumberPagination
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.response import Response

from apps.designacao.models.designacao import Designacao
from apps.designacao.api.serializers.designacao_serializer import DesignacaoSerializer
from apps.designacao.api.filters.designacao_filter import DesignacaoFilter


class DesignacaoPagination(PageNumberPagination):
    page_size = 10
    page_size_query_param = 'page_size'
    max_page_size = 100
    def paginate_queryset(self, queryset, request, view=None):
        no_pagination = request.query_params.get('no_pagination')=="true"
        if no_pagination:
            return None
        return super().paginate_queryset(queryset, request, view)


class DesignacaoViewSet(
    mixins.CreateModelMixin,
    mixins.ListModelMixin,
    mixins.RetrieveModelMixin,
    mixins.DestroyModelMixin,
    mixins.UpdateModelMixin,
    viewsets.GenericViewSet
):
    serializer_class = DesignacaoSerializer
    pagination_class = DesignacaoPagination

    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_class = DesignacaoFilter

    search_fields = [
        'indicado_nome_servidor', 'indicado_nome_civil', 'indicado_rf',
        'titular_nome_servidor', 'titular_rf',
        'unidade_proponente', 'dre_nome', 'numero_portaria',
    ]

    ordering_fields = ['criado_em', 'data_inicio', 'data_fim', 'ano_vigente']

    def get_queryset(self):
        queryset = Designacao.objects.filter(
            is_deleted=False
        ).select_related(
            'impedimento_substituicao'
        ).order_by('-criado_em')

        PAGINATION_PARAMS = {'page', 'page_size', 'format'}
        has_active_filter = bool(
            set(self.request.query_params.keys()) - PAGINATION_PARAMS
        )

        self._limit_to_1000 = not has_active_filter

        return queryset
    
    def list(self, request, *args, **kwargs):        
        base_queryset = self.get_queryset()
        filtered_queryset = self.filter_queryset(base_queryset)

        if getattr(self, '_limit_to_1000', False):
            filtered_queryset = filtered_queryset[:1000]

        no_pagination = request.query_params.get('no_pagination')=="true"
        if no_pagination:
            serializer = self.get_serializer(filtered_queryset, many=True)
            return Response({
                "count": len(serializer.data),
                "next": None,
                "previous": None,
                "results": serializer.data
            })


        page = self.paginate_queryset(filtered_queryset)

        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = self.get_serializer(filtered_queryset, many=True)
        return Response(serializer.data)


    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        instance.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)