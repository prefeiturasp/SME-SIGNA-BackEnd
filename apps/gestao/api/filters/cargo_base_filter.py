"""Filtros para consulta de cargos base.

Permite localizar cargos base por grupamento, descrição resumida,
descrição completa, situação funcional e status.
"""

import django_filters

from apps.gestao.models.cargo_base import CargoBase


class CargoBaseFilter(django_filters.FilterSet):
    """Filtro de cargos base baseado no modelo CargoBase."""

    descricao_resumida = django_filters.CharFilter(
        field_name="descricao_resumida",
        lookup_expr="icontains",
        label="Descrição resumida",
    )
    descricao_completa = django_filters.CharFilter(
        field_name="descricao_completa",
        lookup_expr="icontains",
        label="Descrição completa",
    )
    grupamento = django_filters.ChoiceFilter(
        field_name="grupamento",
        choices=CargoBase.Grupamento.choices,
        label="Grupamento",
    )
    situacao_funcional = django_filters.ChoiceFilter(
        field_name="situacao_funcional",
        choices=CargoBase.SituacaoFuncional.choices,
        label="Situação funcional",
    )
    status = django_filters.ChoiceFilter(
        field_name="status",
        choices=CargoBase.Status.choices,
        label="Status",
    )

    class Meta:
        model = CargoBase
        fields = [
            "grupamento",
            "descricao_resumida",
            "descricao_completa",
            "situacao_funcional",
            "status",
        ]
