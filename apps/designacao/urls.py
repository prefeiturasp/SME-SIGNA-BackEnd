from django.urls import path
from apps.designacao.api.views.designacao_servidor_view import DesignacaoServidorView
from apps.designacao.api.views.designacao_unidades_view import DesignacaoUnidadeView, DesignacaoUnidadeCargosView
from apps.designacao.api.views.designacao import DesignacaoViewSet
from apps.designacao.api.views.designacao_impedimentos_view import ImpedimentoSubstituicaoView
from apps.designacao.api.views.cessacao_view import CessacaoViewSet
from apps.designacao.api.views.insubsistencia_view import InsubsistenciaViewSet
from apps.designacao.api.views.apostila_view import ApostilaViewSet


app_name = "designacao"

urlpatterns = [
    path("servidor", DesignacaoServidorView.as_view(), name="servidor"),
    path("unidade/", DesignacaoUnidadeView.as_view(), name="unidade"),
    path('unidade/cargos/', DesignacaoUnidadeCargosView.as_view(), name='designacao-unidade-cargos'),
    # Acesso as designacoes
    path("designacoes/", DesignacaoViewSet.as_view({'get': 'list', 'post': 'create'}), name="designacoes"),
    # Tipos de Impedimentos
    path("designacoes/impedimentos/", ImpedimentoSubstituicaoView.as_view(), name="impedimentos"),
    # Acesso as designacoes retrieve
    path(
        "designacoes/<int:pk>/", 
        DesignacaoViewSet.as_view({
            'get': 'retrieve', 
            'delete': 'destroy',
            'patch': 'partial_update',
        }), 
        name="designacao-detail"),

    path(
        "designacoes/cargos-base-pareados/",
        DesignacaoViewSet.as_view({'get': 'cargos_base_pareados'}),
        name="cargos-base-pareados"
    ),

    path(
        "designacoes/cargos-sobrepostos-pareados/",
        DesignacaoViewSet.as_view({'get': 'cargos_sobrepostos_pareados'}),
        name="cargos-sobrepostos-pareados"
    ),
    # Acesso às cessações (list e create)
    path(
        "cessacoes/",
        CessacaoViewSet.as_view({'get': 'list', 'post': 'create'}),
        name="cessacoes"
    ),

    # Acesso a uma cessação específica (retrieve e delete)
    path(
        "cessacoes/<int:pk>/",
        CessacaoViewSet.as_view({
            'get': 'retrieve',
            'delete': 'destroy',
        }),
        name="cessacao-detail"
    ),

    # Acesso às insubsistências (list e create)
    path(
        "insubsistencias/",
        InsubsistenciaViewSet.as_view({'get': 'list', 'post': 'create'}),
        name="insubsistencias"
    ),

    # Acesso a uma insubsistência específica (retrieve e delete)
    path(
        "insubsistencias/<int:pk>/",
        InsubsistenciaViewSet.as_view({
            'get': 'retrieve',
         }),
        name="insubsistencia-detail"
    ),

    path(
        "apostilas/",
        ApostilaViewSet.as_view({'get': 'list', 'post': 'create'}),
        name="apostilas"
    ),
    path(
        "apostilas/<int:pk>/",
        ApostilaViewSet.as_view({'get': 'retrieve'}),
        name="apostila-detail"
    ),

    
    ]