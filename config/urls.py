from django.urls import path, include
from django.contrib import admin
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView

urlpatterns = [
    # Endpoints JWT (Simple JWT)
    path('api/token/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('api/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),

    # APIs da sua app (apps.usuarios)
    path('api/usuario/', include('apps.usuarios.urls')),

    # APIs da sua app (apps.alteracao_email)
    path("api/alteracao-email/", include("apps.alteracao_email.urls", namespace="alteracao_email")),

    # APIs da sua app (apps.designacao)
    path("api/designacao/", include("apps.designacao.urls", namespace="designacao")),

    # APIs da sua app (apps.unidades)
    path("api/unidades/", include("apps.unidades.urls", namespace="unidades")),

    # não enviar para produção
    path("admin/", admin.site.urls),
]
