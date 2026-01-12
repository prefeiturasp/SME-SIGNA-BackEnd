import environ
import logging
from django.contrib.auth import get_user_model
from django.db import transaction
from django.utils import timezone

from rest_framework import status, permissions
from rest_framework.exceptions import ValidationError
from rest_framework.response import Response
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.views import TokenObtainPairView

from apps.usuarios.api.serializers.login_serializer import LoginSerializer
from apps.usuarios.services.sme_integracao_service import SmeIntegracaoService
from apps.helpers.exceptions import (
    AuthenticationError,
    SmeIntegracaoException,
    PerfilNaoAutorizadoError
)

User = get_user_model()
logger = logging.getLogger(__name__)
env = environ.Env()


class LoginView(TokenObtainPairView):
    permission_classes = [permissions.AllowAny]

    def post(self, request, *args, **kwargs):
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

            user = self._criar_ou_atualizar_user(login, senha, dados_sme)
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

        except SmeIntegracaoException as e:
            logger.warning("Falha na autenticação: %s", str(e))
            return Response(
                {'detail': 'Parece que estamos com uma instabilidade no momento. Tente entrar novamente daqui a pouco.'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        except PerfilNaoAutorizadoError:
            return Response(
                {
                    "detail": (
                        "Desculpe, mas o acesso ao SIGNA é restrito a perfis específicos."
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
        
    def _valida_perfil_signa(self, dados_sme: dict):
        perfis = dados_sme.get("perfis")

        if not perfis or not isinstance(perfis, list):
            raise PerfilNaoAutorizadoError()

        codigo_signa = env("CODIGO_SISTEMA_SIGNA")

        if codigo_signa not in perfis:
            raise PerfilNaoAutorizadoError()


    def _criar_ou_atualizar_user(self, login, senha, dados_sme):
        """Cria ou atualiza usuário local"""

        with transaction.atomic():
            defaults = {
                "name": dados_sme.get("nome"),
                "email": dados_sme.get("email"),
                "cpf": dados_sme.get("numeroDocumento"),
                "last_login": timezone.now(),
            }

            user, created = User.objects.update_or_create(
                username=login,
                defaults=defaults,
            )

            if created or not user.check_password(senha):
                user.set_password(senha)
                user.save()

            return user

    def _gerar_tokens(self, user):
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
