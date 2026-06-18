"""Views para a listagem de portarias.

Fornece endpoints para filtrar e atualizar portarias exibidas na publicação do
D.O.
"""

from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import filters

from apps.designacao.api.filters.ato_administrativo_filter import (
    AtoAdministrativoFilter,
)
from apps.designacao.api.serializers.ato_administrativo_serializer import (
    AtoAdministrativoListSerializer,
)
from apps.designacao.api.views.designacao_base import DesignacaoBasePagination
from apps.designacao.api.views.portaria import PortariaListViewSet


class AtoAdministrativoListViewSet(PortariaListViewSet):
    """ViewSet para listagem de atos administrativos.

    Exibe atos administrativos de Designação, Cessação,
    Insubsistência e Apostila
    conforme a tela de listagem de atos administrativos.
    """

    serializer_class = AtoAdministrativoListSerializer
    pagination_class = DesignacaoBasePagination

    filter_backends = [
        DjangoFilterBackend,
        filters.SearchFilter,
        filters.OrderingFilter,
    ]
    filterset_class = AtoAdministrativoFilter

    search_fields = [
        "numero_portaria",
        "sei_numero",
        "designacao_detalhe__indicado_nome_servidor",
        "designacao_detalhe__indicado_nome_civil",
        "designacao_detalhe__indicado_rf",
    ]

    ordering_fields = [
        "criado_em",
        "ano_vigente",
        "numero_portaria",
    ]

    ordering = ["numero_portaria"]
