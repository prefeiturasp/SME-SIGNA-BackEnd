from django.urls import path
from apps.usuarios.api.views.login_view import LoginView
from apps.usuarios.api.views.senha_view import EsqueciMinhaSenhaViewSet, RedefinirSenhaViewSet, AtualizarSenhaViewSet
from apps.usuarios.api.views.me_view import MeView

urlpatterns = [
    path("login", LoginView.as_view(), name="login"),
    path("esqueci-senha", view=EsqueciMinhaSenhaViewSet.as_view(), name="esqueci-senha"),
    path('redefinir-senha', view=RedefinirSenhaViewSet.as_view(), name="redefinir-senha"),
    path("atualizar-senha", view=AtualizarSenhaViewSet.as_view(), name="atualizar-senha"),
    path("me", MeView.as_view(), name="me"),
]
