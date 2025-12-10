from django.urls import path, include
from django.contrib import admin
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView

urlpatterns = [
    # Endpoints JWT (Simple JWT)
    path('api/token/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('api/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),

    # APIs da sua app (apps.core)
    path('api/', include('apps.core.urls')),

    # APIs da sua app (apps.usuarios)
    path('api/usuario/', include('apps.usuarios.urls')),


    path("admin/", admin.site.urls),
]
