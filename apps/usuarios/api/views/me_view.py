"""View para recuperar dados do usuário autenticado.

Fornece um endpoint protegido que retorna as informações do perfil do
usuário atual usando o serializer de usuário.
"""

from typing import Any

from django.contrib.auth import get_user_model
from rest_framework import permissions, status
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.usuarios.api.serializers.me_serializer import UserMeSerializer

User = get_user_model()


class MeView(APIView):
    """Retorna os dados do usuário autenticado (requer Bearer access token)."""

    permission_classes = (permissions.IsAuthenticated,)
    serializer_class = UserMeSerializer

    def get(self, request: Request, *args: Any, **kwargs: Any) -> Response:
        """Retorna os dados do usuário autenticado.

        Serializa o usuário atual e devolve os campos de perfil.
        """
        serializer = UserMeSerializer(request.user)
        return Response(serializer.data, status=status.HTTP_200_OK)
