"""Serviço de senha para geração de tokens de redefinição.

Contém utilitários para criar UID e token de reset de senha e expor dados
necessários para o fluxo de recuperação.
"""

import logging

from django.contrib.auth import get_user_model
from django.contrib.auth.tokens import default_token_generator
from django.utils.encoding import force_bytes
from django.utils.http import urlsafe_base64_encode

logger = logging.getLogger(__name__)
User = get_user_model()


class SenhaService:
    """Serviço para lógica de recuperação de senha via nome de usuário."""

    @staticmethod
    def gerar_token_para_usuario(user: User) -> tuple[str, str]:
        """Gera UID e token para reset de senha do usuário.

        Args:
            user (User): Instância do usuário para o qual gerar o token.

        Returns:
            tuple[str, str]: UID codificado em base64 e token de redefinição.
        """
        """
        Gera token e UID para reset de senha.
        """
        token = default_token_generator.make_token(user)
        uid = urlsafe_base64_encode(force_bytes(user.pk))
        return uid, token

    @staticmethod
    def gerar_token_para_reset(username: str, email: str) -> dict:
        """Gera os dados necessários para o fluxo de reset de senha.

        Busca o usuário pelo username, gera UID e token, e retorna o nome
        simplificado para uso no e-mail de recuperação.

        Args:
            username (str): Nome de usuário ou RF do usuário.
            email (str): E-mail do usuário.

        Returns:
            dict: Dados `uid`, `token` e `name` para envio de e-mail.

        Raises:
            User.DoesNotExist: Se o usuário não for encontrado.
        """
        logger.info(f"Iniciando geração de token para usuário: {username}")

        user = User.objects.get(username=username)

        uid, token = SenhaService.gerar_token_para_usuario(user)

        name = user.name.split(" ")[0]

        resultado = {
            "token": token,
            "uid": uid,
            "name": name,
        }

        logger.info(f"Token de reset gerado com sucesso para {username}")
        return resultado
