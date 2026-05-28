"""Views de designação.

Fornece endpoints para listagem, recuperação, criação e atualização de
designações, com suporte a filtros, pesquisa, ordenação e paginação.
"""

from django_filters.rest_framework import DjangoFilterBackend

from rest_framework import filters, mixins, status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from apps.designacao.api.filters.designacao_filter import DesignacaoFilter
from apps.designacao.api.serializers.designacao_serializer import (
    DesignacaoReadSerializer,
    DesignacaoWriteSerializer,
)
from apps.designacao.api.views.designacao_base import (
    DesignacaoBasePagination,
    DesignacaoPaginacaoMixin,
)
from apps.designacao.models.ato_administrativo import AtoAdministrativo
from apps.designacao.services.designacao_service import DesignacaoService

DesignacaoPagination = DesignacaoBasePagination


class DesignacaoViewSet(
    DesignacaoPaginacaoMixin,
    mixins.ListModelMixin,
    mixins.RetrieveModelMixin,
    mixins.DestroyModelMixin,
    viewsets.GenericViewSet,
):
    """ViewSet para designações.

    Expõe list, retrieve, destroy, create e partial_update com filtros,
    pesquisa e ordenação próprios de designações.
    """

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
        """Retorna o queryset base de designações.

        Realiza filtros por tipo de ato administrativo, aplica otimizações
        com `select_related` e `prefetch_related` para reduzir consultas
        ao banco de dados e ordena os resultados por data de criação
        decrescente.

        Returns:
            QuerySet: Queryset otimizado de atos administrativos do tipo
            designação.
        """
        return (
            AtoAdministrativo.objects.filter(
                tipo=AtoAdministrativo.Tipo.DESIGNACAO
            )
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

    # ── List ─────────────────────────────────────────────────────────────────

    def list(self, request, *args, **kwargs):
        """Lista designações conforme filtros e paginação.

        Args:
            request: Requisição HTTP.
            *args: Argumentos posicionais adicionais.
            **kwargs: Argumentos nomeados adicionais.

        Returns:
            Response: Resposta HTTP com a lista de designações.
        """
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

    # ── Create ───────────────────────────────────────────────────────────────

    def create(self, request, *args, **kwargs):
        """Cria uma nova designação.

        Args:
            request: Requisição HTTP contendo os dados da designação.
            *args: Argumentos posicionais adicionais.
            **kwargs: Argumentos nomeados adicionais.

        Returns:
            Response: Resposta HTTP com os dados da designação criada.
        """
        serializer = DesignacaoWriteSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        ato = DesignacaoService.criar(serializer.validated_data)

        ato_com_prefetch = self.get_queryset().filter(pk=ato.pk).first()
        return Response(
            DesignacaoReadSerializer(ato_com_prefetch).data,
            status=status.HTTP_201_CREATED,
        )

    # ── Partial update ───────────────────────────────────────────────────────

    def partial_update(self, request, *args, **kwargs):
        """Atualiza parcialmente uma designação existente.

        Args:
            request: Requisição HTTP contendo os campos a atualizar.
            *args: Argumentos posicionais adicionais.
            **kwargs: Argumentos nomeados adicionais.

        Returns:
            Response: Resposta HTTP com os dados atualizados da designação.
        """
        ato = self.get_object()
        serializer = DesignacaoWriteSerializer(data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)

        ato = DesignacaoService.atualizar(ato, serializer.validated_data)

        ato_atualizado = self.get_queryset().filter(pk=ato.pk).first()
        return Response(DesignacaoReadSerializer(ato_atualizado).data)

    # ── Actions de cargos ────────────────────────────────────────────────────

    @action(detail=False, methods=["get"], url_path="cargos-base-pareados")
    def cargos_base_pareados(self, request):
        """Retorna cargos base pareados entre indicado e titular.

        Args:
            request: Requisição HTTP.

        Returns:
            Response: Lista de cargos base pareados.
        """
        queryset = self.filter_queryset(self.get_queryset()).order_by()
        resultado = DesignacaoService.get_cargos_pareados(
            queryset,
            "designacao_detalhe__indicado_codigo_cargo_base",
            "designacao_detalhe__indicado_cargo_base",
            "designacao_detalhe__titular_codigo_cargo_base",
            "designacao_detalhe__titular_cargo_base",
        )
        return Response(resultado)

    @action(
        detail=False, methods=["get"], url_path="cargos-sobrepostos-pareados"
    )
    def cargos_sobrepostos_pareados(self, request):
        """Retorna cargos sobrepostos pareados entre indicado e titular.

        Args:
            request: Requisição HTTP.

        Returns:
            Response: Lista de cargos sobrepostos pareados.
        """
        queryset = self.filter_queryset(self.get_queryset()).order_by()
        resultado = DesignacaoService.get_cargos_pareados(
            queryset,
            "designacao_detalhe__indicado_codigo_cargo_sobreposto",
            "designacao_detalhe__indicado_cargo_sobreposto",
            "designacao_detalhe__titular_codigo_cargo_sobreposto",
            "designacao_detalhe__titular_cargo_sobreposto",
        )
        return Response(resultado)
