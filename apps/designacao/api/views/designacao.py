from rest_framework import mixins, viewsets, filters
from rest_framework.pagination import PageNumberPagination
from django_filters.rest_framework import DjangoFilterBackend

from apps.designacao.models.designacao import Designacao
from apps.designacao.api.serializers.designacao_serializer import DesignacaoSerializer
from apps.designacao.api.filters.designacao_filter import DesignacaoFilter

class DesignacaoPagination(PageNumberPagination):
    page_size = 10
    page_size_query_param = 'page_size'
    max_page_size = 100

class DesignacaoViewSet(mixins.CreateModelMixin,
                        mixins.ListModelMixin,
                        mixins.RetrieveModelMixin,
                        viewsets.GenericViewSet):
    queryset = Designacao.objects.all().order_by('-criado_em')
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