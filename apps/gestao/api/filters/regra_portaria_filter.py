"""Filtros para consulta de regras de portaria.

Permite localizar regras de portaria por cargo, código EOL, tipo de
módulo e status.
"""

import django_filters

from apps.gestao.models.regra_portaria import RegraPortaria


class RegraPortariaFilter(django_filters.FilterSet):
    """Filtro de regras de portaria baseado no modelo RegraPortaria."""

    cargo = django_filters.CharFilter(
        field_name="descricao_resumida_cargo",
        lookup_expr="icontains",
        label="Cargo",
    )
    codigo_cargo_eol = django_filters.CharFilter(
        field_name="codigo_cargo_eol",
        lookup_expr="icontains",
        label="Código EOL",
    )
    tipo_modulo = django_filters.ChoiceFilter(
        field_name="tipo_modulo",
        choices=RegraPortaria.TipoModulo.choices,
        label="Tipo de módulo",
    )
    status = django_filters.ChoiceFilter(
        field_name="status",
        choices=RegraPortaria.Status.choices,
        label="Status",
    )

    class Meta:
        model = RegraPortaria
        fields = [
            "cargo",
            "codigo_cargo_eol",
            "tipo_modulo",
            "status",
        ]
