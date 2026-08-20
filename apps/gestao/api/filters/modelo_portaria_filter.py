"""Filtros para consulta de modelos de portaria.

Permite localizar modelos de portaria por tipo de portaria, status,
tipo de cargo e nome do modelo.
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

    class Meta:
        model = ModeloPortaria
        fields = [
            "nome_modelo",
            "tipo_portaria",
            "status",
            "tipo_cargo",
        ]
