from django.urls import path

from apps.designacao.api.views.designacao_legado import DesignacaoLegadoViewSet
from apps.designacao.api.views.designacao_impedimentos_view import (
    ImpedimentoSubstituicaoView,
)
from apps.designacao.api.views.designacao_servidor_view import DesignacaoServidorView
from apps.designacao.api.views.designacao_unidades_view import (
    DesignacaoUnidadeView,
    DesignacaoUnidadeCargosView,
)
from apps.designacao.api.views.cessacao_view import CessacaoViewSet
from apps.designacao.api.views.insubsistencia_view import InsubsistenciaViewSet
from apps.designacao.api.views.apostila_view import ApostilaViewSet
from apps.designacao.api.views.portaria import PortariaListViewSet


app_name = "designacao"

urlpatterns = [
    path("servidor", DesignacaoServidorView.as_view(), name="servidor"),
    path("unidade/", DesignacaoUnidadeView.as_view(), name="unidade"),
    path(
        "unidade/cargos/",
        DesignacaoUnidadeCargosView.as_view(),
        name="designacao-unidade-cargos",
    ),
    # Designações (legado — modelo Designacao)
    path(
        "designacoes/",
        DesignacaoLegadoViewSet.as_view({"get": "list", "post": "create"}),
        name="designacoes",
    ),
    path(
        "designacoes/impedimentos/",
        ImpedimentoSubstituicaoView.as_view(),
        name="impedimentos",
    ),
    path(
        "designacoes/<int:pk>/",
        DesignacaoLegadoViewSet.as_view(
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
        DesignacaoLegadoViewSet.as_view({"get": "cargos_base_pareados"}),
        name="cargos-base-pareados",
    ),
    path(
        "designacoes/cargos-sobrepostos-pareados/",
        DesignacaoLegadoViewSet.as_view({"get": "cargos_sobrepostos_pareados"}),
        name="cargos-sobrepostos-pareados",
    ),
    # Cessações (legado — modelo Cessacao)
    path(
        "cessacoes/",
        CessacaoViewSet.as_view({"get": "list", "post": "create"}),
        name="cessacoes",
    ),
    path(
        "cessacoes/<int:pk>/",
        CessacaoViewSet.as_view({"get": "retrieve", "delete": "destroy"}),
        name="cessacao-detail",
    ),
    # Insubsistências (legado — modelo Insubsistencia)
    path(
        "insubsistencias/",
        InsubsistenciaViewSet.as_view({"get": "list", "post": "create"}),
        name="insubsistencias",
    ),
    path(
        "insubsistencias/<int:pk>/",
        InsubsistenciaViewSet.as_view({"get": "retrieve"}),
        name="insubsistencia-detail",
    ),
    # Apostilas (legado — modelo Apostila)
    path(
        "apostilas/",
        ApostilaViewSet.as_view({"get": "list", "post": "create"}),
        name="apostilas",
    ),
    path(
        "apostilas/<int:pk>/",
        ApostilaViewSet.as_view({"get": "retrieve"}),
        name="apostila-detail",
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
]
