# apps/core/urls.py
from django.urls import path
from . import views

urlpatterns = [
    path('profile/', views.profile, name='api-profile'),
    path('debug-headers/', views.debug_headers, name='debug-headers'),  # temporário
    path('debug-auth/', views.debug_authenticate, name='debug-auth'), # temporário
]
