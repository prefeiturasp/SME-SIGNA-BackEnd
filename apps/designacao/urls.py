from django.urls import path
from apps.designacao.api.views.designacao_servidor_view import DesignacaoServidorView

app_name = "designacao"

urlpatterns = [
    path("servidor", DesignacaoServidorView.as_view(), name="servidor"),
]
