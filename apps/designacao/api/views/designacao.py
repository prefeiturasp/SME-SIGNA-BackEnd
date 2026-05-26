from rest_framework import mixins, viewsets, filters, status
from rest_framework.decorators import action
from rest_framework.pagination import PageNumberPagination
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend

from apps.designacao.models.ato_administrativo import AtoAdministrativo
from apps.designacao.api.serializers.designacao_serializer import (
    DesignacaoReadSerializer,
    DesignacaoWriteSerializer,
)
from apps.designacao.api.filters.designacao_filter import DesignacaoFilter
from apps.designacao.services.designacao_service import DesignacaoService


class DesignacaoPagination(PageNumberPagination):
    page_size = 10
    page_size_query_param = "page_size"
    max_page_size = 100

    def paginate_queryset(self, queryset, request, view=None):
        if request.query_params.get("no_pagination", "").lower() == "true":
            return None
        return super().paginate_queryset(queryset, request, view)


class DesignacaoViewSet(
    mixins.ListModelMixin,
    mixins.RetrieveModelMixin,
    mixins.DestroyModelMixin,
    viewsets.GenericViewSet,
):
    serializer_class = DesignacaoReadSerializer
    pagination_class = DesignacaoPagination

    filter_backends = [
        DjangoFilterBackend,
        filters.SearchFilter,
        filters.OrderingFilter,
    ]
    filterset_class = DesignacaoFilter

    search_fields = [
        "designacao_detalhe__indicado_nome_servidor",
        "designacao_detalhe__indicado_nome_civil",
        "designacao_detalhe__indicado_rf",
        "designacao_detalhe__titular_nome_servidor",
        "designacao_detalhe__titular_rf",
        "designacao_detalhe__unidade_proponente",
        "designacao_detalhe__dre_nome",
        "numero_portaria",
    ]

    ordering_fields = [
        "criado_em",
        "ano_vigente",
        "designacao_detalhe__data_inicio",
        "designacao_detalhe__data_fim",
    ]

    def get_queryset(self):
        return (
            AtoAdministrativo.objects.filter(tipo=AtoAdministrativo.Tipo.DESIGNACAO)
            .select_related(
                "designacao_detalhe",
                "designacao_detalhe__impedimento_substituicao",
            )
            .prefetch_related(
                "filhos",
                "filhos__filhos",
                "filhos__cessacao_detalhe",
                "filhos__apostila_detalhe",
                "filhos__apostila_detalhe__alteracoes",
                "filhos__insubsistencia_detalhe",
            )
            .order_by("-criado_em")
        )

    # ── Helpers de paginação ──────────────────────────────────────────────────

    def _is_no_pagination(self):
        return self.request.query_params.get("no_pagination", "").lower() == "true"

    def _has_filters(self):
        PAGINATION_PARAMS = {"page", "page_size", "format", "no_pagination"}
        return bool(set(self.request.query_params.keys()) - PAGINATION_PARAMS)

    def _should_limit_queryset(self):
        return not self._has_filters() and not self._is_no_pagination()

    # ── List ──────────────────────────────────────────────────────────────────

    def list(self, request, *args, **kwargs):
        queryset = self.filter_queryset(self.get_queryset())

        if self._is_no_pagination():
            return Response(DesignacaoReadSerializer(queryset, many=True).data)

        if self._should_limit_queryset():
            queryset = queryset[:1000]

        page = self.paginate_queryset(queryset)
        if page is not None:
            return self.get_paginated_response(
                DesignacaoReadSerializer(page, many=True).data
            )

        return Response(DesignacaoReadSerializer(queryset, many=True).data)

    # ── Create ────────────────────────────────────────────────────────────────

    def create(self, request, *args, **kwargs):
        serializer = DesignacaoWriteSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        ato = DesignacaoService.criar(serializer.validated_data)

        ato_com_prefetch = self.get_queryset().filter(pk=ato.pk).first()
        return Response(
            DesignacaoReadSerializer(ato_com_prefetch).data,
            status=status.HTTP_201_CREATED,
        )

    # ── Partial update ────────────────────────────────────────────────────────

    def partial_update(self, request, *args, **kwargs):
        ato = self.get_object()
        serializer = DesignacaoWriteSerializer(data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)

        ato = DesignacaoService.atualizar(ato, serializer.validated_data)

        ato_atualizado = self.get_queryset().filter(pk=ato.pk).first()
        return Response(DesignacaoReadSerializer(ato_atualizado).data)

    # ── Actions de cargos ─────────────────────────────────────────────────────

    @action(detail=False, methods=["get"], url_path="cargos-base-pareados")
    def cargos_base_pareados(self, request):
        queryset = self.filter_queryset(self.get_queryset()).order_by()
        resultado = DesignacaoService.get_cargos_pareados(
            queryset,
            "designacao_detalhe__indicado_codigo_cargo_base",
            "designacao_detalhe__indicado_cargo_base",
            "designacao_detalhe__titular_codigo_cargo_base",
            "designacao_detalhe__titular_cargo_base",
        )
        return Response(resultado)

    @action(detail=False, methods=["get"], url_path="cargos-sobrepostos-pareados")
    def cargos_sobrepostos_pareados(self, request):
        queryset = self.filter_queryset(self.get_queryset()).order_by()
        resultado = DesignacaoService.get_cargos_pareados(
            queryset,
            "designacao_detalhe__indicado_codigo_cargo_sobreposto",
            "designacao_detalhe__indicado_cargo_sobreposto",
            "designacao_detalhe__titular_codigo_cargo_sobreposto",
            "designacao_detalhe__titular_cargo_sobreposto",
        )
        return Response(resultado)
