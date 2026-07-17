from django.urls import path

from apps.designacao.api.views.apostila_view import ApostilaViewSet
from apps.designacao.api.views.ato_administrativo_view import (
    AtoAdministrativoListViewSet,
)
from apps.designacao.api.views.cessacao_view import CessacaoViewSet
from apps.designacao.api.views.designacao import DesignacaoViewSet
from apps.designacao.api.views.designacao_impedimentos_view import (
    ImpedimentoSubstituicaoView,
)
from apps.designacao.api.views.designacao_servidor_view import (
    DesignacaoServidorView,
)
from apps.designacao.api.views.designacao_unidades_view import (
    DesignacaoUnidadeCargosView,
    DesignacaoUnidadeView,
)
from apps.designacao.api.views.insubsistencia_view import (
    InsubsistenciaViewSet,
)
from apps.designacao.api.views.portaria import PortariaListViewSet

app_name = "designacao"

urlpatterns = [
    # Utilitários
    path("servidor", DesignacaoServidorView.as_view(), name="servidor"),
    path("unidade/", DesignacaoUnidadeView.as_view(), name="unidade"),
    path(
        "unidade/cargos/",
        DesignacaoUnidadeCargosView.as_view(),
        name="unidade-cargos",
    ),
    # Designações (AtoAdministrativo + DesignacaoDetalhe)
    path(
        "designacoes/",
        DesignacaoViewSet.as_view({"get": "list", "post": "create"}),
        name="designacoes",
    ),
    path(
        "designacoes/impedimentos/",
        ImpedimentoSubstituicaoView.as_view(),
        name="impedimentos",
    ),
    path(
        "designacoes/<int:pk>/",
        DesignacaoViewSet.as_view(
            {
                "get": "retrieve",
                "delete": "destroy",
                "patch": "partial_update",
            }
        ),
        name="designacao-detail",
    ),
    path(
        "designacoes/cargos-base-pareados/",
        DesignacaoViewSet.as_view({"get": "cargos_base_pareados"}),
        name="cargos-base-pareados",
    ),
    path(
        "designacoes/cargos-sobrepostos-pareados/",
        DesignacaoViewSet.as_view({"get": "cargos_sobrepostos_pareados"}),
        name="cargos-sobrepostos-pareados",
    ),
    path(
        "designacoes/buscar-por-portaria/",
        DesignacaoViewSet.as_view({"get": "buscar_por_portaria"}),
        name="designacao-buscar-por-portaria",
    ),
    # Cessações (AtoAdministrativo + CessacaoDetalhe)
    path(
        "cessacoes/",
        CessacaoViewSet.as_view({"get": "list", "post": "create"}),
        name="cessacoes",
    ),
    path(
        "cessacoes/<int:pk>/",
        CessacaoViewSet.as_view(
            {
                "get": "retrieve",
                "delete": "destroy",
            }
        ),
        name="cessacao-detail",
    ),
    path(
        "cessacoes/buscar-por-portaria/",
        CessacaoViewSet.as_view({"get": "buscar_por_portaria"}),
        name="cessacao-buscar-por-portaria",
    ),
    # Apostilas (AtoAdministrativo + ApostilaDetalhe)
    path(
        "apostilas/",
        ApostilaViewSet.as_view({"get": "list", "post": "create"}),
        name="apostilas",
    ),
    path(
        "apostilas/<int:pk>/",
        ApostilaViewSet.as_view(
            {
                "get": "retrieve",
                "delete": "destroy",
            }
        ),
        name="apostila-detail",
    ),
    # Insubsistências (AtoAdministrativo + InsubsistenciaDetalhe)
    path(
        "insubsistencias/",
        InsubsistenciaViewSet.as_view({"get": "list", "post": "create"}),
        name="insubsistencias",
    ),
    path(
        "insubsistencias/<int:pk>/",
        InsubsistenciaViewSet.as_view(
            {
                "get": "retrieve",
                "delete": "destroy",
            }
        ),
        name="insubsistencia-detail",
    ),
    path(
        "insubsistencias/buscar-por-portaria/",
        InsubsistenciaViewSet.as_view({"get": "buscar_por_portaria"}),
        name="insubsistencia-buscar-por-portaria",
    ),
    # Portarias — listagem para publicação no D.O.
    path(
        "portarias/",
        PortariaListViewSet.as_view({"get": "list"}),
        name="portarias",
    ),
    path(
        "portarias/atualizar-data-publicacao/",
        PortariaListViewSet.as_view({"post": "atualizar_data_publicacao"}),
        name="portarias-atualizar-data-publicacao",
    ),
    # Atos Administrativos — listagem de atos administrativos
    path(
        "atos-administrativos/",
        AtoAdministrativoListViewSet.as_view({"get": "list"}),
        name="atos-administrativos",
    ),
]
