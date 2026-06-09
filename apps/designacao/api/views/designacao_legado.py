"""Views legadas de designação.

Fornece endpoints para CRUD de designações legadas, com filtros,
pesquisa, ordenação e ações auxiliares para cargos pareados.
"""

from django.db.models import QuerySet
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import filters, mixins, viewsets
from rest_framework.decorators import action
from rest_framework.request import Request
from rest_framework.response import Response

from apps.designacao.api.filters.designacao_legado_filter import (
    DesignacaoLegadoFilter,
)
from apps.designacao.api.serializers.designacao_legado_serializer import (
    DesignacaoLegadoSerializer,
)
from apps.designacao.api.views.designacao_base import (
    DesignacaoBasePagination,
    DesignacaoPaginacaoMixin,
)
from apps.designacao.models.designacao import Designacao
from apps.designacao.services.designacao_service import DesignacaoService

DesignacaoLegadoPagination = DesignacaoBasePagination


class DesignacaoLegadoViewSet(
    DesignacaoPaginacaoMixin,
    mixins.CreateModelMixin,
    mixins.ListModelMixin,
    mixins.RetrieveModelMixin,
    mixins.DestroyModelMixin,
    mixins.UpdateModelMixin,
    viewsets.GenericViewSet,
):
    """ViewSet para designações legadas.

    Expõe create, list, retrieve, update e destroy com suporte a filtros,
    pesquisa e ordenação próprias de designações legadas.
    """

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

    def get_queryset(self) -> QuerySet:
        """Retorna o queryset base para designações legadas.

        Returns:
            QuerySet: Designações não deletadas com carregamento de
            relacionamentos.
        """
        return (
            Designacao.objects.filter(is_deleted=False)
            .select_related("impedimento_substituicao", "cessacao")
            .order_by("-criado_em")
        )

    def list(self, request: Request, *args, **kwargs) -> Response:
        """Lista designações legadas conforme filtros e paginação.

        Args:
            request: Requisição HTTP.
            *args: Argumentos posicionais adicionais.
            **kwargs: Argumentos nomeados adicionais.

        Returns:
            Response: Resposta HTTP com a lista de designações.
        """
        queryset = self.filter_queryset(self.get_queryset())

        if self._is_no_pagination():
            return Response(
                DesignacaoLegadoSerializer(queryset, many=True).data
            )

        if self._should_limit_queryset():
            queryset = queryset[:1000]

        page = self.paginate_queryset(queryset)
        if page is not None:
            return self.get_paginated_response(
                DesignacaoLegadoSerializer(page, many=True).data
            )

        return Response(DesignacaoLegadoSerializer(queryset, many=True).data)

    @action(detail=False, methods=["get"], url_path="cargos-base-pareados")
    def cargos_base_pareados(self, request: Request) -> Response:
        """Retorna cargos base pareados entre indicado e titular.

        Args:
            request: Requisição HTTP.

        Returns:
            Response: Lista de cargos base pareados.
        """
        queryset = self.filter_queryset(self.get_queryset()).order_by()
        resultado = DesignacaoService.get_cargos_pareados(
            queryset,
            "indicado_codigo_cargo_base",
            "indicado_cargo_base",
            "titular_codigo_cargo_base",
            "titular_cargo_base",
        )
        return Response(resultado)

    @action(
        detail=False, methods=["get"], url_path="cargos-sobrepostos-pareados"
    )
    def cargos_sobrepostos_pareados(self, request: Request) -> Response:
        """Retorna cargos sobrepostos pareados entre indicado e titular.

        Args:
            request: Requisição HTTP.

        Returns:
            Response: Lista de cargos sobrepostos pareados.
        """
        queryset = self.filter_queryset(self.get_queryset()).order_by()
        resultado = DesignacaoService.get_cargos_pareados(
            queryset,
            "indicado_codigo_cargo_sobreposto",
            "indicado_cargo_sobreposto",
            "titular_codigo_cargo_sobreposto",
            "titular_cargo_sobreposto",
        )
        return Response(resultado)
