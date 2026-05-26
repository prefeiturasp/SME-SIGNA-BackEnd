"""Filtros para pesquisa de designações em AtoAdministrativo.

Contém filtros customizados para busca por RF, nome e código de cargo base, além de
filtros por período, cargo sobreposto, DRE, unidade, ano e impedimentos de substituição.
"""

from django.db import models
import django_filters

from apps.designacao.models.ato_administrativo import AtoAdministrativo
from apps.designacao.models.designacao import ImpedimentoSubstituicao


class DesignacaoFilter(django_filters.FilterSet):
    """Filtro de designações baseado no modelo AtoAdministrativo.

    Este filtro permite combinar buscas por RF, nome e cargo base com diversos campos
    relacionados ao detalhe da designação.
    """

    rf = django_filters.CharFilter(method='filter_rf')
    nome = django_filters.CharFilter(method='filter_nome')
    cargo_base = django_filters.NumberFilter(method='filter_cargo_base')

    periodo = django_filters.DateFromToRangeFilter(
        field_name='designacao_detalhe__data_inicio'
    )
    cargo_sobreposto = django_filters.NumberFilter(
        field_name='designacao_detalhe__cargo_vaga'
    )
    dre = django_filters.CharFilter(
        field_name='designacao_detalhe__dre_nome',
        lookup_expr='icontains',
    )
    unidade = django_filters.CharFilter(
        field_name='designacao_detalhe__unidade_proponente',
        lookup_expr='icontains',
    )
    ano = django_filters.CharFilter(
        field_name='ano_vigente',
        lookup_expr='exact',
    )
    impedimento_substituicao = django_filters.ModelChoiceFilter(
        field_name='designacao_detalhe__impedimento_substituicao',
        queryset=ImpedimentoSubstituicao.objects.all(),
    )
    impedimento_codigo = django_filters.CharFilter(
        field_name='designacao_detalhe__impedimento_substituicao__codigo',
        lookup_expr='exact',
    )

    def filter_rf(self, queryset, name, value):
        """Filtra designações pelo número de RF.

        Args:
            queryset: Queryset de AtoAdministrativo a ser filtrado.
            name: Nome do campo de filtro.
            value: Valor da RF buscada.

        Returns:
            Queryset filtrado com correspondências por RF de indicado ou titular.
        """
        return queryset.filter(
            models.Q(designacao_detalhe__indicado_rf=value)
            | models.Q(designacao_detalhe__titular_rf=value)
        )

    def filter_nome(self, queryset, name, value):
        """Filtra designações pelo nome do servidor.

        Args:
            queryset: Queryset de AtoAdministrativo a ser filtrado.
            name: Nome do campo de filtro.
            value: Parte ou nome completo do servidor.

        Returns:
            Queryset filtrado com correspondências por nome de indicado ou titular.
        """
        return queryset.filter(
            models.Q(designacao_detalhe__indicado_nome_servidor__icontains=value)
            | models.Q(designacao_detalhe__titular_nome_servidor__icontains=value)
        )

    def filter_cargo_base(self, queryset, name, value):
        """Filtra designações pelo código de cargo base.

        Args:
            queryset: Queryset de AtoAdministrativo a ser filtrado.
            name: Nome do campo de filtro.
            value: Código do cargo base.

        Returns:
            Queryset filtrado com correspondências por cargo base de indicado ou titular.
        """
        return queryset.filter(
            models.Q(designacao_detalhe__indicado_codigo_cargo_base=value)
            | models.Q(designacao_detalhe__titular_codigo_cargo_base=value)
        )

    class Meta:
        model = AtoAdministrativo
        fields = [
            'rf', 'nome', 'periodo', 'cargo_base', 'cargo_sobreposto',
            'dre', 'unidade', 'ano',
            'impedimento_substituicao', 'impedimento_codigo',
        ]
