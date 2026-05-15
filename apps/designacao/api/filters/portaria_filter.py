import django_filters

from apps.designacao.models.ato_administrativo import AtoAdministrativo


class PortariaFilter(django_filters.FilterSet):

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

    def filter_tipo(self, queryset, name, value):
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
