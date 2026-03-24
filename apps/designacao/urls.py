from django.urls import path
from apps.designacao.api.views.designacao_servidor_view import DesignacaoServidorView
from apps.designacao.api.views.designacao_unidades_view import DesignacaoUnidadeView, DesignacaoUnidadeCargosView
from apps.designacao.api.views.designacao import DesignacaoViewSet
from apps.designacao.api.views.designacao_impedimentos_view import ImpedimentoSubstituicaoView


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
    path("designacoes/<int:pk>/", DesignacaoViewSet.as_view({'get': 'retrieve'}), name="designacao-detail"),
]