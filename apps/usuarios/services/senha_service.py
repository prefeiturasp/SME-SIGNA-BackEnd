"""Serviço de senha para geração de tokens de redefinição.

Contém utilitários para criar UID e token de reset de senha e expor dados
necessários para o fluxo de recuperação.
"""

import logging

from django.contrib.auth import get_user_model
from django.contrib.auth.tokens import default_token_generator
from django.db import IntegrityError, transaction
from django.utils.encoding import force_bytes
from django.utils.http import urlsafe_base64_encode

from apps.helpers.exceptions import EmailNaoCadastradoError
from apps.usuarios.models import User

logger = logging.getLogger(__name__)
UserModel = get_user_model()


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
        token = default_token_generator.make_token(user)
        uid = urlsafe_base64_encode(force_bytes(user.pk))
        return uid, token

    @staticmethod
    def gerar_token_para_reset(
        username: str,
        email: str,
    ) -> dict[str, str]:
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
        logger.info(
            "Iniciando geração de token para usuário: %s",
            username,
        )

        user = UserModel.objects.get(username=username)

        uid, token = SenhaService.gerar_token_para_usuario(user)

        name = user.name.split(" ")[0]

        resultado = {
            "token": token,
            "uid": uid,
            "name": name,
        }

        logger.info(
            "Token de reset gerado com sucesso para %s",
            username,
        )
        return resultado

    @staticmethod
    def buscar_usuario_local(username: str) -> User | None:
        """Busca o usuário local pelo username.

        Args:
            username (str): Nome de usuário ou RF do usuário.

        Returns:
            User | None: Instância do usuário ou None se não encontrado.

        """
        return UserModel.objects.filter(username=username).first()

    @staticmethod
    def atualizar_senha_local(user: User, nova_senha: str) -> None:
        """Atualiza a senha do usuário no banco local.

        Args:
            user (User): Instância do usuário a ser atualizado.
            nova_senha (str): Nova senha em texto plano.

        """
        user.set_password(nova_senha)
        user.save(update_fields=["password"])

    @staticmethod
    def sincronizar_usuario_local(username: str, dados_sme: dict) -> User:
        """Cria ou atualiza o usuário local com dados retornados pela SME.

        Args:
            username (str): Nome de usuário ou RF do usuário.
            dados_sme (dict): Dados do usuário retornados pela SME.

        Returns:
            User: Instância do usuário criado ou atualizado.

        Raises:
            EmailNaoCadastradoError: Quando há conflito de integridade ao
            salvar (ex: e-mail duplicado).

        """
        logger.info("Sincronizando usuário local para %s", username)

        nome = dados_sme.get("nome")
        if not nome:
            logger.warning(
                "Dados SME sem nome para %s, pulando sincronização", username
            )
            return UserModel.objects.get(username=username)

        try:
            with transaction.atomic():
                user, created = UserModel.objects.update_or_create(
                    username=username,
                    defaults={
                        "name": nome,
                        "email": dados_sme.get("email", ""),
                        "cpf": dados_sme.get("numeroDocumento", ""),
                    },
                )

            action = "criado" if created else "atualizado"
            logger.info("Usuário %s %s localmente", username, action)
            return user

        except IntegrityError as exc:
            logger.error(
                "Falha ao sincronizar usuário %s: %s",
                username,
                str(exc),
            )
            raise EmailNaoCadastradoError(
                "Já existe um usuário com este e-mail. <br/>"
                "Entre em contato com o administrador do sistema."
            ) from exc
