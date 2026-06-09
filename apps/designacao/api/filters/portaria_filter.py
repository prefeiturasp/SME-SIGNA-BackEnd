"""Filtros para pesquisa de portarias em AtoAdministrativo.

Inclui filtros por intervalo de portaria, ano vigente, tipo de ato, número SEI,
informações de designação de servidor e data de cessação.
"""

import django_filters
from django.db import models

from apps.designacao.models.ato_administrativo import AtoAdministrativo


class PortariaFilter(django_filters.FilterSet):
    """Filtro de portarias baseado no modelo AtoAdministrativo.

    Este filtro oferece critérios para localizar portarias por número, tipo,
    ano,
    servidor, unidade e data de cessação.
    """

    portaria_inicial = django_filters.CharFilter(
        field_name="numero_portaria",
        lookup_expr="gte",
        label="Portaria inicial",
    )
    portaria_final = django_filters.CharFilter(
        field_name="numero_portaria",
        lookup_expr="lte",
        label="Portaria final",
    )
    ano = django_filters.CharFilter(
        field_name="ano_vigente",
        lookup_expr="exact",
        label="Ano vigente",
    )
    TIPO_CHOICES = AtoAdministrativo.Tipo.choices + [
        ("DESIGNACAO_CESSACAO", "Designação e Cessação"),
    ]

    tipo = django_filters.ChoiceFilter(
        field_name="tipo",
        choices=TIPO_CHOICES,
        label="Tipo de ato",
        method="filter_tipo",
    )
    numero_sei = django_filters.CharFilter(
        field_name="sei_numero",
        lookup_expr="icontains",
        label="Nº SEI",
    )
    # Filtros via DesignacaoDetalhe
    nome = django_filters.CharFilter(
        field_name="designacao_detalhe__indicado_nome_servidor",
        lookup_expr="icontains",
        label="Nome do servidor",
    )
    rf = django_filters.CharFilter(
        field_name="designacao_detalhe__indicado_rf",
        lookup_expr="exact",
        label="RF do servidor",
    )
    dre = django_filters.CharFilter(
        field_name="designacao_detalhe__dre_nome",
        lookup_expr="icontains",
        label="DRE",
    )
    unidade = django_filters.CharFilter(
        field_name="designacao_detalhe__unidade_proponente",
        lookup_expr="icontains",
        label="Unidade proponente",
    )
    # Filtro por data de cessação
    data_cessacao = django_filters.DateFilter(
        field_name="cessacao_detalhe__data_cessacao",
        lookup_expr="exact",
        label="Data de cessação",
    )

    def filter_tipo(
        self, queryset: models.QuerySet, name: str, value: str
    ) -> models.QuerySet:
        """Filtra portarias pelo tipo de ato.

        Args:
            queryset: Queryset de AtoAdministrativo a ser filtrado.
            name: Nome do campo de filtro.
            value: Valor do tipo de ato buscado.

        Returns:
            Queryset filtrado com o tipo de ato selecionado.

        """
        if value == "DESIGNACAO_CESSACAO":
            return queryset.filter(tipo__in=["DESIGNACAO", "CESSACAO"])
        return queryset.filter(tipo=value)

    class Meta:
        model = AtoAdministrativo
        fields = [
            "portaria_inicial",
            "portaria_final",
            "ano",
            "tipo",
            "numero_sei",
            "nome",
            "rf",
            "dre",
            "unidade",
            "data_cessacao",
        ]
