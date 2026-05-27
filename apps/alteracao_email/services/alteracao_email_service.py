"""Serviço para gerenciar solicitações e validação de alteração de e-mail.

Este módulo provê operações para solicitar uma alteração de e-mail,
criar o token de confirmação, enviar o e-mail de validação e validar o token
antes de efetivar a alteração.
"""

import logging

import environ

from django.shortcuts import get_object_or_404
from django.utils.timezone import now, timedelta

from apps.alteracao_email.models.alteracao_email import AlteracaoEmail
from apps.helpers.exceptions import (
    TokenExpiradoException,
    TokenJaUtilizadoException,
)
from apps.usuarios.services.envia_email_service import EnviaEmailService

env = environ.Env()
logger = logging.getLogger(__name__)


class AlteracaoEmailService:
    """Serviços de negócio para alteração de e-mail.

    Esta classe centraliza a lógica de solicitação de alteração de e-mail e a
    validação do token de confirmação gerado para o processo.
    """

    @staticmethod
    def solicitar(usuario, novo_email):
        """Solicita a alteração de e-mail e envia o e-mail de confirmação.

        Args:
            usuario (User): O usuário que solicitou a alteração de e-mail.
            novo_email (str): O novo endereço de e-mail para o usuário.

        Returns:
            AlteracaoEmail: A instância criada da solicitação de alteração de
            e-mail.
        """

        email_request = AlteracaoEmail.objects.create(
            usuario=usuario, novo_email=novo_email
        )

        validation_link = (
            f"{env('AMBIENTE_URL')}/confirmar-email/{email_request.token}"
        )
        logger.info(f"Link de validação gerado: {validation_link}")

        EnviaEmailService.enviar(
            destinatario=novo_email,
            assunto="Alteração de e-mail",
            template_html="emails/alteracao_email.html",
            contexto={"usuario_nome": usuario.name, "link": validation_link},
        )

        return email_request

    @staticmethod
    def validar(token):
        """Valida o token de alteração de e-mail e retorna a solicitação.

        Args:
            token (uuid.UUID|str): O token de confirmação associado à
            solicitação.

        Returns:
            tuple[User, AlteracaoEmail]: O usuário e a solicitação de alteração
                de e-mail correspondente ao token.

        Raises:
            TokenJaUtilizadoException: Se o token já foi utilizado.
            TokenExpiradoException: Se o token expirou.
            Http404: Se a solicitação não for encontrada.
        """

        email_request = get_object_or_404(AlteracaoEmail, token=token)
        usuario = email_request.usuario

        if email_request.ja_usado:
            raise TokenJaUtilizadoException("Este token já foi utilizado.")

        if email_request.criado_em < now() - timedelta(minutes=30):
            raise TokenExpiradoException("Token expirado.")

        logger.info(f"E-mail alterado com sucesso: {usuario.email}")
        return usuario, email_request
