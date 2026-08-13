from django.urls import path

from apps.gestao.api.views.cargo_base_view import (
    CargoBaseViewSet,
    CargoEolView,
)

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
]
