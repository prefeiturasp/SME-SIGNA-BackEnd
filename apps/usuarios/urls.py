from django.urls import path
from apps.usuarios.api.views.login_view import LoginView

urlpatterns = [
    path("login", LoginView.as_view(), name="login"),
]
