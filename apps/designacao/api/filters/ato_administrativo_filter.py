"""Filtros para pesquisa de portarias em AtoAdministrativo.

Inclui filtros por intervalo de portaria, ano vigente, tipo de ato, número SEI,
informações de designação de servidor e data de cessação.
"""

import django_filters
from django.db import models

from apps.designacao.api.filters.portaria_filter import PortariaFilter
from apps.designacao.models.ato_administrativo import AtoAdministrativo


class AtoAdministrativoFilter(PortariaFilter):
    """Filtro de atos administrativos baseado no modelo AtoAdministrativo.

    Este filtro oferece critérios para localizar
    atos administrativos por número, tipo, ano,
    servidor, unidade e data de cessação.
    """

    portaria = django_filters.CharFilter(
        field_name="numero_portaria",
        lookup_expr="exact",
        label="Portaria",
    )
    nome_titular_e_indicado = django_filters.CharFilter(
        field_name="nome_titular_e_indicado",
        label="Nome do titular e indicado",
        method="filter_nome_titular_e_indicado",
    )

    observacao = django_filters.CharFilter(
        field_name="observacao",
        label="Observação",
        method="filter_observacao",
    )

    status_publicacao = django_filters.ChoiceFilter(
        field_name="status_publicacao",
        choices=AtoAdministrativo.StatusPublicacao.choices,
        label="Status de publicação",
    )

    rf = django_filters.CharFilter(method="filter_rf")

    periodo = django_filters.DateFromToRangeFilter(field_name="criado_em")
    TIPO_CHOICES = AtoAdministrativo.Tipo.choices + [
        ("DESIGNACAO_CESSACAO", "Designação e Cessação"),
        ("INSUBSISTENCIA_DESIGNACAO", "Insubsistência de Designação"),
        ("INSUBSISTENCIA_CESSACAO", "Insubsistência de Cessação"),
        ("APOSTILA_DESIGNACAO", "Apostila de Designação"),
        ("APOSTILA_CESSACAO", "Apostila de Cessação"),
        ("INSUBSISTENCIA_APOSTILA", "Insubsistência de Apostila"),
        ("INSUBSISTENCIA_INSUBSISTENCIA", "Tornar sem efeito"),
    ]

    tipo = django_filters.ChoiceFilter(
        field_name="tipo",
        choices=TIPO_CHOICES,
        label="Tipo de ato",
        method="filter_tipo",
    )

    ato_id = django_filters.NumberFilter(
        field_name="ato_id",
        label="ID do ato",
        method="filter_ato_id",
    )

    def filter_rf(
        self, queryset: models.QuerySet, name: str, value: str
    ) -> models.QuerySet:
        """Filtra designações pelo número de RF.

        Args:
            queryset: Queryset de AtoAdministrativo a ser filtrado.
            name: Nome do campo de filtro.
            value: Valor da RF buscada.

        Returns:
            Queryset filtrado com correspondências por RF de indicado ou
            titular.

        """
        return queryset.filter(
            models.Q(designacao_detalhe__indicado_rf=value)
            | models.Q(designacao_detalhe__titular_rf=value)
        )

    def filter_nome_titular_e_indicado(
        self, queryset: models.QuerySet, name: str, value: str
    ) -> models.QuerySet:
        """Filtra atos administrativos pelo nome do titular e indicado.

        Args:
            queryset: Queryset de AtoAdministrativo a ser filtrado.
            name: Nome do campo de filtro.
            value: Valor do nome do titular e indicado buscado.

        Returns:
            Queryset filtrado com o nome do titular e indicado selecionados.

        """
        queryset = queryset.filter(
            models.Q(
                designacao_detalhe__titular_nome_servidor__icontains=value
            )
            | models.Q(designacao_detalhe__titular_nome_civil__icontains=value)
            | models.Q(
                designacao_detalhe__indicado_nome_servidor__icontains=value
            )
            | models.Q(
                designacao_detalhe__indicado_nome_civil__icontains=value
            )
        )
        return queryset

    def filter_observacao(
        self, queryset: models.QuerySet, name: str, value: str
    ) -> models.QuerySet:
        """Filtra atos administrativos pela observação.

        Args:
            queryset: Queryset de AtoAdministrativo a ser filtrado.
            name: Nome do campo de filtro.
            value: Valor da observação buscada.

        Returns:
            Queryset filtrado com a observação selecionada.

        """
        queryset = queryset.filter(
            models.Q(apostila_detalhe__observacao__icontains=value)
            | models.Q(insubsistencia_detalhe__observacoes__icontains=value)
        )
        return queryset

    def filter_ato_id(
        self, queryset: models.QuerySet, name: str, value: int
    ) -> models.QuerySet:
        """Filtra atos administrativos relacionados a um id do ato.

        Args:
            queryset: Queryset de AtoAdministrativo a ser filtrado.
            name: Nome do campo de filtro.
            value: Valor do id do ato buscado.

        Returns:
            Queryset filtrado com o ato relacionado ao id selecionado.

        """
        queryset = queryset.filter(
            models.Q(ato_pai_id=value) | models.Q(ato_raiz_id=value)
        )
        return queryset

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
        elif "_" in value:
            tipo, pai = value.split("_")
            return queryset.filter(tipo=tipo, ato_pai__tipo=pai)

        return queryset.filter(tipo=value)

    class Meta:
        model = AtoAdministrativo
        fields = [
            "tipo",
            "periodo",
            "portaria",
            "nome_titular_e_indicado",
            "status_publicacao",
            "rf",
            "numero_sei",
            "ato_id",
            "observacao",
        ]
