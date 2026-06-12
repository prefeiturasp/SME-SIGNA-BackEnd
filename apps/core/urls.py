from django.urls import path

from apps.core.api.views.health_view import HealthView

urlpatterns = [
    path("health/", HealthView.as_view(), name="health"),
]
