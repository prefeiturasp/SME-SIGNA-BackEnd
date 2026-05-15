from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import filters, mixins, viewsets
from rest_framework.decorators import action
from rest_framework.pagination import PageNumberPagination
from rest_framework.response import Response

from apps.designacao.api.filters.designacao_legado_filter import DesignacaoLegadoFilter
from apps.designacao.api.serializers.designacao_legado_serializer import (
    DesignacaoLegadoSerializer,
)
from apps.designacao.models.designacao import Designacao
from apps.designacao.services.designacao_service import DesignacaoService


class DesignacaoLegadoPagination(PageNumberPagination):
    page_size = 10
    page_size_query_param = "page_size"
    max_page_size = 100

    def paginate_queryset(self, queryset, request, view=None):
        if request.query_params.get("no_pagination", "").lower() == "true":
            return None
        return super().paginate_queryset(queryset, request, view)


class DesignacaoLegadoViewSet(
    mixins.CreateModelMixin,
    mixins.ListModelMixin,
    mixins.RetrieveModelMixin,
    mixins.DestroyModelMixin,
    mixins.UpdateModelMixin,
    viewsets.GenericViewSet,
):
    serializer_class = DesignacaoLegadoSerializer
    pagination_class = DesignacaoLegadoPagination

    filter_backends = [
        DjangoFilterBackend,
        filters.SearchFilter,
        filters.OrderingFilter,
    ]
    filterset_class = DesignacaoLegadoFilter

    search_fields = [
        "indicado_nome_servidor",
        "indicado_nome_civil",
        "indicado_rf",
        "titular_nome_servidor",
        "titular_rf",
        "unidade_proponente",
        "dre_nome",
        "numero_portaria",
    ]

    ordering_fields = ["criado_em", "data_inicio", "data_fim", "ano_vigente"]

    def get_queryset(self):
        return (
            Designacao.objects.filter(is_deleted=False)
            .select_related("impedimento_substituicao", "cessacao")
            .order_by("-criado_em")
        )

    def _is_no_pagination(self):
        return self.request.query_params.get("no_pagination", "").lower() == "true"

    def _has_filters(self):
        PAGINATION_PARAMS = {"page", "page_size", "format", "no_pagination"}
        return bool(set(self.request.query_params.keys()) - PAGINATION_PARAMS)

    def _should_limit_queryset(self):
        return not self._has_filters() and not self._is_no_pagination()

    def list(self, request, *args, **kwargs):
        queryset = self.filter_queryset(self.get_queryset())

        if self._is_no_pagination():
            return Response(DesignacaoLegadoSerializer(queryset, many=True).data)

        if self._should_limit_queryset():
            queryset = queryset[:1000]

        page = self.paginate_queryset(queryset)
        if page is not None:
            return self.get_paginated_response(
                DesignacaoLegadoSerializer(page, many=True).data
            )

        return Response(DesignacaoLegadoSerializer(queryset, many=True).data)

    @action(detail=False, methods=["get"], url_path="cargos-base-pareados")
    def cargos_base_pareados(self, request):
        queryset = self.filter_queryset(self.get_queryset()).order_by()
        resultado = DesignacaoService.get_cargos_pareados(
            queryset,
            "indicado_codigo_cargo_base",
            "indicado_cargo_base",
            "titular_codigo_cargo_base",
            "titular_cargo_base",
        )
        return Response(resultado)

    @action(detail=False, methods=["get"], url_path="cargos-sobrepostos-pareados")
    def cargos_sobrepostos_pareados(self, request):
        queryset = self.filter_queryset(self.get_queryset()).order_by()
        resultado = DesignacaoService.get_cargos_pareados(
            queryset,
            "indicado_codigo_cargo_sobreposto",
            "indicado_cargo_sobreposto",
            "titular_codigo_cargo_sobreposto",
            "titular_cargo_sobreposto",
        )
        return Response(resultado)
