"""Filtros do histórico de designações por unidade escolar.

Os filtros incidem sobre as **designações** (itens de primeiro nível da
resposta). Os atos derivados continuam sendo devolvidos por inteiro em
``atos_relacionados``, pois o histórico de uma designação só faz sentido
completo.

Reaproveita a nomenclatura já usada no sistema: ``tipo``,
``status_publicacao`` e ``observacao`` vêm de ``AtoAdministrativoFilter``;
``periodo`` (com os params ``periodo_after``/``periodo_before``) vem de
``DesignacaoFilter``.
"""

import django_filters
from django.db import models

from apps.designacao.api.filters.ato_administrativo_filter import (
    AtoAdministrativoFilter,
)
from apps.designacao.models.ato_administrativo import AtoAdministrativo


class HistoricoDesignacaoFilter(django_filters.FilterSet):
    """Filtro do histórico de designações de uma unidade escolar.

    Todos os parâmetros são opcionais e combináveis (``E`` lógico).
    Aplicado ao queryset de designações da UE, define quais designações
    entram na resposta.
    """

    TIPO_CHOICES = AtoAdministrativoFilter.TIPO_CHOICES

    tipo = django_filters.ChoiceFilter(
        field_name="tipo",
        choices=TIPO_CHOICES,
        label="Tipo de ato",
        method="filter_tipo",
    )

    cargo = django_filters.NumberFilter(
        field_name="designacao_detalhe__cargo_vaga",
        label="Código do cargo da vaga",
    )

    status_publicacao = django_filters.ChoiceFilter(
        field_name="status_publicacao",
        choices=AtoAdministrativo.StatusPublicacao.choices,
        label="Status de publicação",
    )

    # Gera os parâmetros `periodo_after` e `periodo_before`.
    periodo = django_filters.DateFromToRangeFilter(
        field_name="designacao_detalhe__data_inicio",
        label="Período da designação (data de início)",
    )

    observacao = django_filters.CharFilter(
        method="filter_observacao",
        label="Observação de ato relacionado",
    )

    def filter_tipo(
        self, queryset: models.QuerySet, name: str, value: str
    ) -> models.QuerySet:
        """Mantém as designações que possuem o tipo de ato informado.

        O histórico lista designações. ``DESIGNACAO`` e
        ``DESIGNACAO_CESSACAO`` casam com a própria designação, como a
        união desses tipos na listagem de atos. Os demais valores casam
        com um ato derivado: ``CESSACAO``, ``APOSTILA`` e
        ``INSUBSISTENCIA`` pelo tipo, e os valores com pai
        (``APOSTILA_DESIGNACAO``, ``INSUBSISTENCIA_APOSTILA`` etc.) pelo
        tipo do ato e do pai.

        Args:
            queryset: Queryset de designações (``AtoAdministrativo``).
            name: Nome do campo de filtro.
            value: Tipo de ato, no mesmo formato de
                ``AtoAdministrativoFilter``.

        Returns:
            Queryset das designações que atendem ao tipo.

        """
        if value in {"DESIGNACAO", "DESIGNACAO_CESSACAO"}:
            return queryset

        relacionados = AtoAdministrativo.objects.exclude(
            ato_raiz_id__isnull=True
        )
        if "_" in value:
            tipo, pai = value.split("_")
            relacionados = relacionados.filter(tipo=tipo, ato_pai__tipo=pai)
        else:
            relacionados = relacionados.filter(tipo=value)
        return queryset.filter(pk__in=relacionados.values("ato_raiz_id"))

    def filter_observacao(
        self, queryset: models.QuerySet, name: str, value: str
    ) -> models.QuerySet:
        """Filtra designações que têm um ato relacionado com a observação.

        A observação existe apenas nos detalhes de apostila
        (``observacao``) e de insubsistência (``observacoes``). Como todo
        descendente aponta para a designação de origem em ``ato_raiz``,
        basta subconsultar esses atos e manter as designações cujo ``pk``
        aparece como raiz.

        Args:
            queryset: Queryset de designações (``AtoAdministrativo``).
            name: Nome do campo de filtro.
            value: Trecho da observação buscada (case-insensitive).

        Returns:
            Queryset filtrado pelas designações com observação
            correspondente em algum ato relacionado.

        """
        ids_raiz = (
            AtoAdministrativo.objects.filter(
                models.Q(apostila_detalhe__observacao__icontains=value)
                | models.Q(
                    insubsistencia_detalhe__observacoes__icontains=value
                )
            )
            .exclude(ato_raiz_id__isnull=True)
            .values("ato_raiz_id")
        )
        return queryset.filter(pk__in=ids_raiz)

    class Meta:
        model = AtoAdministrativo
        fields = [
            "tipo",
            "cargo",
            "status_publicacao",
            "periodo",
            "observacao",
        ]
