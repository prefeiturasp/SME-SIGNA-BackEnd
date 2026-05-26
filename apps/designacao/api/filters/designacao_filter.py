from django.db import models
import django_filters

from apps.designacao.models.ato_administrativo import AtoAdministrativo
from apps.designacao.models.designacao import ImpedimentoSubstituicao


class DesignacaoFilter(django_filters.FilterSet):

    rf = django_filters.CharFilter(method="filter_rf")
    nome = django_filters.CharFilter(method="filter_nome")
    cargo_base = django_filters.NumberFilter(method="filter_cargo_base")

    periodo = django_filters.DateFromToRangeFilter(
        field_name="designacao_detalhe__data_inicio"
    )
    cargo_sobreposto = django_filters.NumberFilter(
        field_name="designacao_detalhe__cargo_vaga"
    )
    dre = django_filters.CharFilter(
        field_name="designacao_detalhe__dre_nome",
        lookup_expr="icontains",
    )
    unidade = django_filters.CharFilter(
        field_name="designacao_detalhe__unidade_proponente",
        lookup_expr="icontains",
    )
    ano = django_filters.CharFilter(
        field_name="ano_vigente",
        lookup_expr="exact",
    )
    impedimento_substituicao = django_filters.ModelChoiceFilter(
        field_name="designacao_detalhe__impedimento_substituicao",
        queryset=ImpedimentoSubstituicao.objects.all(),
    )
    impedimento_codigo = django_filters.CharFilter(
        field_name="designacao_detalhe__impedimento_substituicao__codigo",
        lookup_expr="exact",
    )

    def filter_rf(self, queryset, name, value):
        return queryset.filter(
            models.Q(designacao_detalhe__indicado_rf=value)
            | models.Q(designacao_detalhe__titular_rf=value)
        )

    def filter_nome(self, queryset, name, value):
        return queryset.filter(
            models.Q(designacao_detalhe__indicado_nome_servidor__icontains=value)
            | models.Q(designacao_detalhe__titular_nome_servidor__icontains=value)
        )

    def filter_cargo_base(self, queryset, name, value):
        return queryset.filter(
            models.Q(designacao_detalhe__indicado_codigo_cargo_base=value)
            | models.Q(designacao_detalhe__titular_codigo_cargo_base=value)
        )

    class Meta:
        model = AtoAdministrativo
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
