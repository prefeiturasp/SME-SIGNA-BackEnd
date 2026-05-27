"""Viewsets de API para solicitações e validação de alteração de e-mail.

Este módulo define viewsets do Django REST Framework para solicitar a
alteração de e-mail e validar o token de alteração. Ele coordena a
validação do serializer, serviços de lógica de negócio e integração com o
serviço SME.
"""

import logging

from django.db import transaction
from rest_framework import status, viewsets
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from apps.alteracao_email.api.serializers.alteracao_email_serializer import (
    AlteracaoEmailSerializer,
)
from apps.alteracao_email.services.alteracao_email_service import AlteracaoEmailService
from apps.helpers.exceptions import (
    SmeIntegracaoException,
    TokenExpiradoException,
    TokenJaUtilizadoException,
)
from apps.usuarios.services.sme_integracao_service import SmeIntegracaoService

logger = logging.getLogger(__name__)


class SolicitarAlteracaoEmailViewSet(viewsets.ViewSet):
    """Gerencia solicitações para iniciar a alteração de e-mail do usuário autenticado.

    O viewset recebe o novo endereço de e-mail, valida-o pelo serializer e
    delega a criação da solicitação de alteração de e-mail à camada de serviço.
    """

    permission_classes = [IsAuthenticated]

    def create(self, request):
        """Cria uma solicitação de alteração de e-mail para o usuário autenticado.

        Args:
            request (rest_framework.request.Request): A requisição recebida que
                contém o novo e-mail e o usuário autenticado.

        Returns:
            rest_framework.response.Response: Uma resposta com status 201 se o
                e-mail de confirmação foi enviado com sucesso, ou 500 em caso de
                erro inesperado.
        """

        serializer = AlteracaoEmailSerializer(
            data=request.data, context={"request": request}
        )
        serializer.is_valid(raise_exception=True)

        try:
            AlteracaoEmailService.solicitar(
                usuario=request.user, novo_email=serializer.validated_data["new_email"]
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
    """Gerencia a validação de tokens de alteração de e-mail e finaliza a alteração.

    Este viewset valida o token fornecido, atualiza o e-mail do usuário no
    serviço de integração SME e marca a solicitação de alteração de e-mail
    como utilizada.
    """

    permission_classes = [IsAuthenticated]

    def update(self, request, pk=None):
        """Valida um token de alteração de e-mail e aplica a atualização do e-mail.

        Args:
            request (rest_framework.request.Request): A requisição recebida.
            pk (str|int): O identificador do token usado para validar a alteração
                de e-mail.

        Returns:
            rest_framework.response.Response: Uma resposta com status 200 se o
                e-mail foi alterado com sucesso, 400 em caso de erro de validação
                ou integração, ou 500 para erros inesperados.
        """

        try:
            with transaction.atomic():
                usuario, email_request = AlteracaoEmailService.validar(pk)

                SmeIntegracaoService.altera_email(
                    usuario.username, email_request.novo_email
                )

                usuario.email = email_request.novo_email
                usuario.save()

                email_request.ja_usado = True
                email_request.save()

                return Response(
                    {"message": "E-mail alterado com sucesso.", "email": usuario.email},
                    status=status.HTTP_200_OK,
                )

        except TokenJaUtilizadoException as e:
            return Response({"detail": str(e)}, status=status.HTTP_400_BAD_REQUEST)

        except TokenExpiradoException as e:
            return Response({"detail": str(e)}, status=status.HTTP_400_BAD_REQUEST)

        except SmeIntegracaoException as e:
            logger.error(
                "Erro na integração SME para alteração de email do usuário ID %s: %s",
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
