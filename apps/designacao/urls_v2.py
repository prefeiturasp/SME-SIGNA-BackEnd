from django.urls import path

from apps.designacao.api.views.designacao import DesignacaoViewSet
from apps.designacao.api.views.designacao_impedimentos_view import ImpedimentoSubstituicaoView
from apps.designacao.api.views.designacao_servidor_view import DesignacaoServidorView
from apps.designacao.api.views.designacao_unidades_view import (
    DesignacaoUnidadeView,
    DesignacaoUnidadeCargosView,
)
from apps.designacao.api.views.v2.cessacao_view import CessacaoV2ViewSet

app_name = "designacao_v2"

urlpatterns = [
    # Utilitários (mesmas views do legado)
    path("servidor", DesignacaoServidorView.as_view(), name="servidor"),
    path("unidade/", DesignacaoUnidadeView.as_view(), name="unidade"),
    path("unidade/cargos/", DesignacaoUnidadeCargosView.as_view(), name="unidade-cargos"),

    # Designações (nova modelagem — AtoAdministrativo + DesignacaoDetalhe)
    path(
        "designacoes/",
        DesignacaoViewSet.as_view({'get': 'list', 'post': 'create'}),
        name="designacoes",
    ),
    path(
        "designacoes/impedimentos/",
        ImpedimentoSubstituicaoView.as_view(),
        name="impedimentos",
    ),
    path(
        "designacoes/<int:pk>/",
        DesignacaoViewSet.as_view({
            'get': 'retrieve',
            'delete': 'destroy',
            'patch': 'partial_update',
        }),
        name="designacao-detail",
    ),
    path(
        "designacoes/cargos-base-pareados/",
        DesignacaoViewSet.as_view({'get': 'cargos_base_pareados'}),
        name="cargos-base-pareados",
    ),
    path(
        "designacoes/cargos-sobrepostos-pareados/",
        DesignacaoViewSet.as_view({'get': 'cargos_sobrepostos_pareados'}),
        name="cargos-sobrepostos-pareados",
    ),

    # Cessações (nova modelagem — AtoAdministrativo + CessacaoDetalhe)
    path(
        "cessacoes/",
        CessacaoV2ViewSet.as_view({'get': 'list', 'post': 'create'}),
        name="cessacoes",
    ),
    path(
        "cessacoes/<int:pk>/",
        CessacaoV2ViewSet.as_view({
            'get': 'retrieve',
            'delete': 'destroy',
        }),
        name="cessacao-detail",
    ),
]
