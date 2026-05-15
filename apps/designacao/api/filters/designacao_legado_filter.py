import django_filters
from django.db import models

from apps.designacao.models.designacao import Designacao, ImpedimentoSubstituicao


class DesignacaoLegadoFilter(django_filters.FilterSet):

    rf = django_filters.CharFilter(method="filter_rf")
    nome = django_filters.CharFilter(method="filter_nome")
    cargo_base = django_filters.NumberFilter(method="filter_cargo_base")
    periodo = django_filters.DateFromToRangeFilter(field_name="data_inicio")
    cargo_sobreposto = django_filters.NumberFilter(field_name="cargo_vaga")
    dre = django_filters.CharFilter(field_name="dre_nome", lookup_expr="icontains")
    unidade = django_filters.CharFilter(
        field_name="unidade_proponente", lookup_expr="icontains"
    )
    ano = django_filters.CharFilter(field_name="ano_vigente", lookup_expr="exact")

    impedimento_substituicao = django_filters.ModelChoiceFilter(
        queryset=ImpedimentoSubstituicao.objects.all()
    )
    impedimento_codigo = django_filters.CharFilter(
        field_name="impedimento_substituicao__codigo",
        lookup_expr="exact",
    )

    def filter_rf(self, queryset, name, value):
        return queryset.filter(models.Q(indicado_rf=value) | models.Q(titular_rf=value))

    def filter_nome(self, queryset, name, value):
        return queryset.filter(
            models.Q(indicado_nome_servidor__icontains=value)
            | models.Q(titular_nome_servidor__icontains=value)
        )

    def filter_cargo_base(self, queryset, name, value):
        return queryset.filter(
            models.Q(indicado_codigo_cargo_base=value)
            | models.Q(titular_codigo_cargo_base=value)
        )

    class Meta:
        model = Designacao
        fields = [
            "rf",
            "nome",
            "periodo",
            "cargo_base",
            "cargo_sobreposto",
            "dre",
            "unidade",
            "ano",
            "impedimento_substituicao",
            "impedimento_codigo",
        ]
