from django.urls import path

from apps.gestao.api.views.cargo_base_view import (
    CargoBaseViewSet,
    CargoEolView,
)
from apps.gestao.api.views.modelo_portaria_view import (
    ModeloPortariaVariaveisView,
    ModeloPortariaViewSet,
)
from apps.gestao.api.views.regra_portaria_view import RegraPortariaViewSet

app_name = "gestao"

urlpatterns = [
    path(
        "cargos-base/",
        CargoBaseViewSet.as_view({"get": "list", "post": "create"}),
        name="cargos-base",
    ),
    path(
        "cargos-base/<int:pk>/",
        CargoBaseViewSet.as_view(
            {"get": "retrieve", "patch": "partial_update"}
        ),
        name="cargos-base-detail",
    ),
    path(
        "cargos-eol/",
        CargoEolView.as_view(),
        name="cargos-eol",
    ),
    path(
        "modelos-portaria/",
        ModeloPortariaViewSet.as_view({"get": "list", "post": "create"}),
        name="modelos-portaria",
    ),
    path(
        "modelos-portaria/variaveis/",
        ModeloPortariaVariaveisView.as_view(),
        name="modelos-portaria-variaveis",
    ),
    path(
        "modelos-portaria/<int:pk>/",
        ModeloPortariaViewSet.as_view({"get": "retrieve"}),
        name="modelos-portaria-detail",
    ),
    path(
        "regras-portaria/",
        RegraPortariaViewSet.as_view({"get": "list", "post": "create"}),
        name="regras-portaria",
    ),
    path(
        "regras-portaria/<int:pk>/",
        RegraPortariaViewSet.as_view(
            {"get": "retrieve", "patch": "partial_update"}
        ),
        name="regras-portaria-detail",
    ),
]
