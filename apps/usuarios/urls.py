from django.urls import path
from apps.usuarios.api.views.login_view import LoginView
from apps.usuarios.api.views.senha_view import EsqueciMinhaSenhaViewSet

urlpatterns = [
    path("login", LoginView.as_view(), name="login"),
    path("esqueci-senha", view=EsqueciMinhaSenhaViewSet.as_view(), name="esqueci-senha"),
]
