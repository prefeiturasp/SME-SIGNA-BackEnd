"""Viewsets de API para solicitações e validação de alteração de e-mail.

Este módulo define viewsets do Django REST Framework para solicitar a
alteração de e-mail e validar o token de alteração. Ele coordena a
validação do serializer, serviços de lógica de negócio e integração com o
serviço SME.
"""

import logging

from django.db import transaction
from django.http import Http404
from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import (
    OpenApiParameter,
    extend_schema,
    inline_serializer,
)
from rest_framework import serializers, status, viewsets
from rest_framework.permissions import IsAuthenticated
from rest_framework.request import Request
from rest_framework.response import Response

from apps.alteracao_email.api.serializers.alteracao_email_serializer import (
    AlteracaoEmailSerializer,
)
from apps.alteracao_email.services.alteracao_email_service import (
    AlteracaoEmailService,
)
from apps.helpers.exceptions import (
    SmeIntegracaoError,
    TokenExpiradoError,
    TokenJaUtilizadoError,
)
from apps.usuarios.models import User
from apps.usuarios.services.sme_integracao_service import SmeIntegracaoService

logger = logging.getLogger(__name__)


class SolicitarAlteracaoEmailViewSet(viewsets.ViewSet):
    """Gerencia solicitações de alteração de e-mail do usuário autenticado.

    O viewset recebe o novo endereço de e-mail, valida-o pelo serializer e
    delega a criação da solicitação de alteração de e-mail à camada de serviço.
    """

    permission_classes = [IsAuthenticated]

    @extend_schema(
        request=AlteracaoEmailSerializer,
        responses={
            201: inline_serializer(
                "SolicitarAlteracaoEmailResponse",
                fields={"message": serializers.CharField()},
            ),
            401: inline_serializer(
                "SolicitarAlteracaoEmailNaoAutenticadoResponse",
                fields={"detail": serializers.CharField()},
            ),
            500: inline_serializer(
                "SolicitarAlteracaoEmailErroResponse",
                fields={"detail": serializers.CharField()},
            ),
        },
    )
    def create(self, request: Request) -> Response:
        """Cria uma solicitação de alteração de e-mail.

        Args:
            request (rest_framework.request.Request): A requisição recebida que
                contém o novo e-mail e o usuário autenticado.

        Returns:
            rest_framework.response.Response: Uma resposta com status 201 se o
                e-mail de confirmação foi enviado com sucesso, ou 500 em caso
                de erro inesperado.

        """
        if not isinstance(request.user, User):
            return Response(
                {"detail": "Usuário não autenticado."},
                status=status.HTTP_401_UNAUTHORIZED,
            )
        usuario = request.user

        serializer = AlteracaoEmailSerializer(
            data=request.data, context={"request": request}
        )
        serializer.is_valid(raise_exception=True)

        try:
            AlteracaoEmailService.solicitar(
                usuario=usuario,
                novo_email=serializer.validated_data["new_email"],
            )

            return Response(
                {"message": "E-mail de confirmação enviado com sucesso."},
                status=status.HTTP_201_CREATED,
            )

        except Exception:
            return Response(
                {"detail": "Erro inesperado."},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )


class ValidarAlteracaoEmailViewSet(viewsets.ViewSet):
    """Gerencia a validação de tokens de alteração de e-mail.

    Este viewset valida o token fornecido, atualiza o e-mail do usuário no
    serviço de integração SME e marca a solicitação de alteração de e-mail
    como utilizada.
    """

    permission_classes = [IsAuthenticated]

    @extend_schema(
        request=None,
        parameters=[
            OpenApiParameter(
                name="id",
                type=OpenApiTypes.UUID,
                location=OpenApiParameter.PATH,
                description="Token de alteração de e-mail.",
            ),
        ],
        responses={
            200: inline_serializer(
                "ValidarAlteracaoEmailResponse",
                fields={
                    "message": serializers.CharField(),
                    "email": serializers.EmailField(),
                },
            ),
            400: inline_serializer(
                "ValidarAlteracaoEmailErroResponse",
                fields={"detail": serializers.CharField()},
            ),
            404: inline_serializer(
                "ValidarAlteracaoEmailNaoEncontradoResponse",
                fields={"detail": serializers.CharField()},
            ),
            500: inline_serializer(
                "ValidarAlteracaoEmailErroInternoResponse",
                fields={"detail": serializers.CharField()},
            ),
        },
    )
    def update(self, request: Request, pk: str | None = None) -> Response:
        """Valida um token de alteração de e-mail e aplica a atualização.

        Args:
            request (rest_framework.request.Request): A requisição recebida.
            pk (str|int): O identificador do token usado para validar a
            alteração de e-mail.

        Returns:
            rest_framework.response.Response: Uma resposta com status 200 se o
                e-mail foi alterado com sucesso, 400 em caso de erro de
                validação ou integração, 404 se o token não existir, ou 500
                para erros inesperados.

        """
        if pk is None:
            return Response(
                {"detail": "Token não informado."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            with transaction.atomic():
                usuario, email_request = AlteracaoEmailService.validar(pk)

                SmeIntegracaoService.altera_email(
                    usuario.username,
                    email_request.novo_email,
                )

                usuario.email = email_request.novo_email
                usuario.save()

                email_request.ja_usado = True
                email_request.save()

                return Response(
                    {
                        "message": "E-mail alterado com sucesso.",
                        "email": usuario.email,
                    },
                    status=status.HTTP_200_OK,
                )

        except Http404:
            return Response(
                {"detail": "Token não encontrado."},
                status=status.HTTP_404_NOT_FOUND,
            )

        except TokenJaUtilizadoError as e:
            return Response(
                {"detail": str(e)},
                status=status.HTTP_400_BAD_REQUEST,
            )

        except TokenExpiradoError as e:
            return Response(
                {"detail": str(e)},
                status=status.HTTP_400_BAD_REQUEST,
            )

        except SmeIntegracaoError as e:
            logger.error(
                "Erro na integração SME para alteração de email "
                "do usuário ID %s: %s",
                usuario,
                str(e),
            )
            return Response(
                {"detail": str(e)},
                status=status.HTTP_400_BAD_REQUEST,
            )

        except Exception:
            return Response(
                {"detail": "Erro inesperado."},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )
