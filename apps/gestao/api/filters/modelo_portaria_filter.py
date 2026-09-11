"""Filtros para consulta de modelos de portaria.

Permite localizar modelos de portaria por tipo de portaria, tipo de
ato pai, status, tipo de cargo, nome do modelo e data de criação.
"""

import django_filters

from apps.designacao.models.ato_administrativo import AtoAdministrativo
from apps.gestao.models.modelo_portaria import ModeloPortaria


class ModeloPortariaFilter(django_filters.FilterSet):
    """Filtro de modelos de portaria baseado no modelo ModeloPortaria."""

    nome_modelo = django_filters.CharFilter(
        field_name="nome_modelo",
        lookup_expr="icontains",
        label="Nome do modelo",
    )
    tipo_portaria = django_filters.ChoiceFilter(
        field_name="tipo_portaria",
        choices=AtoAdministrativo.Tipo.choices,
        label="Tipo de portaria",
    )
    tipo_ato_pai = django_filters.ChoiceFilter(
        field_name="tipo_ato_pai",
        choices=AtoAdministrativo.Tipo.choices,
        label="Tipo do ato pai",
    )
    status = django_filters.ChoiceFilter(
        field_name="status",
        choices=ModeloPortaria.Status.choices,
        label="Status",
    )
    tipo_cargo = django_filters.ChoiceFilter(
        field_name="tipo_cargo",
        choices=ModeloPortaria.TipoCargo.choices,
        label="Tipo de cargo",
    )
    criado_em = django_filters.DateFromToRangeFilter(
        field_name="criado_em",
        label="Data de criação",
    )

    class Meta:
        model = ModeloPortaria
        fields = [
            "nome_modelo",
            "tipo_portaria",
            "tipo_ato_pai",
            "status",
            "tipo_cargo",
            "criado_em",
        ]
