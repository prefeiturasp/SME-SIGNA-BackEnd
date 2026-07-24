"""Views de autenticação de usuários.

Este módulo contém a view de login que autentica o usuário contra a SME,
valida o perfil, sincroniza o usuário local e retorna tokens JWT.
"""

import logging
from typing import Any

import environ
from rest_framework import permissions, status
from rest_framework.exceptions import ValidationError
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.views import TokenObtainPairView

from apps.helpers.exceptions import (
    AuthenticationError,
    PerfilNaoAutorizadoError,
    SmeIntegracaoError,
)
from apps.usuarios.api.serializers.login_serializer import LoginSerializer
from apps.usuarios.models import User
from apps.usuarios.services.sme_integracao_service import SmeIntegracaoService

logger = logging.getLogger(__name__)
env = environ.Env()


class LoginView(TokenObtainPairView):
    """View de login que emite tokens JWT para usuários autenticados.

    A view valida credenciais, consulta a SME, valida perfis autorizados,
    sincroniza o usuário local e devolve os tokens de acesso e refresh.
    """

    # Respita configuração global de permissões, permitindo acesso anônimo
    permission_classes = (permissions.AllowAny,)  # type: ignore[assignment]

    def post(self, request: Request, *args: Any, **kwargs: Any) -> Response:
        """Processa o login do usuário e retorna tokens JWT.

        Valida as credenciais, autentica na SME, verifica o perfil do usuário,
        sincroniza o usuário local e retorna os tokens de acesso e refresh.
        """
        serializer = LoginSerializer(data=request.data)

        try:
            serializer.is_valid(raise_exception=True)
        except ValidationError:
            return Response(
                {"detail": "Credenciais inválidas"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        login = serializer.validated_data["username"]
        senha = serializer.validated_data["password"]

        try:
            dados_sme = SmeIntegracaoService.autentica(login, senha)

            self._valida_perfil_signa(dados_sme)

            user = SmeIntegracaoService.sincronizar_usuario_local(
                login,
                senha,
                dados_sme,
            )
            tokens = self._gerar_tokens(user)

            return Response(
                {
                    "token": tokens["access"],
                    "name": user.name,
                    "email": user.email,
                    "cpf": user.cpf,
                },
                status=status.HTTP_200_OK,
            )

        except AuthenticationError:
            return Response(
                {"detail": "Usuário ou senha inválidos"},
                status=status.HTTP_401_UNAUTHORIZED,
            )

        except SmeIntegracaoError as e:
            logger.warning("Falha na autenticação: %s", str(e))
            return Response(
                {
                    "detail": (
                        "Parece que estamos com uma instabilidade "
                        "no momento. Tente entrar novamente daqui a pouco."
                    )
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        except PerfilNaoAutorizadoError:
            return Response(
                {
                    "detail": (
                        "Desculpe, mas o acesso ao SIGNA é "
                        "restrito a perfis específicos."
                    )
                },
                status=status.HTTP_401_UNAUTHORIZED,
            )

        except Exception as e:
            logger.error("Erro interno login: %s", e)
            return Response(
                {"detail": "Erro interno"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

    def _valida_perfil_signa(self, dados_sme: dict) -> None:
        """Valida se o usuário possui perfil autorizado no SIGNA."""
        perfis = dados_sme.get("perfis")

        if not perfis or not isinstance(perfis, list):
            raise PerfilNaoAutorizadoError()

        perfis_normalizados = [p.upper() for p in perfis]
        perfil_signa = env("GUIDE_PERFIL_SIGNA")

        if perfil_signa not in perfis_normalizados:
            raise PerfilNaoAutorizadoError()

    def _gerar_tokens(self, user: User) -> dict[str, str]:
        """Gera tokens JWT personalizados para o usuário."""
        refresh = RefreshToken.for_user(user)

        refresh["username"] = user.username
        refresh["name"] = user.name or ""
        refresh["email"] = user.email or ""

        access = refresh.access_token
        access["username"] = user.username
        access["name"] = user.name or ""
        access["email"] = user.email or ""

        return {
            "refresh": str(refresh),
            "access": str(access),
        }
