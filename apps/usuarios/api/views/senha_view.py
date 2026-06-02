"""Views de recuperação e alteração de senha.

Inclui endpoints para iniciar o fluxo de "esqueci minha senha",
redefinir senha via UID/token e alterar senha de usuário autenticado.
"""

import logging

import environ

from django.contrib.auth import get_user_model
from django.db import IntegrityError, transaction
from rest_framework import permissions, status
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.helpers.exceptions import (
    EmailNaoCadastradoError,
    SmeIntegracaoError,
    UserNotFoundError,
)
from apps.helpers.utils import anonimizar_email
from apps.usuarios.api.serializers.senha_serializer import (
    AtualizarSenhaSerializer,
    EsqueciMinhaSenhaSerializer,
    RedefinirSenhaSerializer,
)
from apps.usuarios.services.envia_email_service import EnviaEmailService
from apps.usuarios.services.senha_service import SenhaService
from apps.usuarios.services.sme_integracao_service import SmeIntegracaoService

logger = logging.getLogger(__name__)
User = get_user_model()
env = environ.Env()


class EsqueciMinhaSenhaViewSet(APIView):
    """View para iniciar o fluxo de recuperação de senha.

    Recebe o nome de usuário e envia um e-mail com o link de redefinição.
    """

    permission_classes = [AllowAny]

    MENSAGEM_EMAIL_NAO_CADASTRADO = (
        "E-mail não encontrado! <br/>"
        "Para resolver este problema, entre em contato com o administrador do sistema."  # noqa: E501
    )
    MENSAGEM_USUARIO_NAO_ENCONTRADO = "Usuário não encontrado"
    MENSAGEM_ERRO_INTERNO = "Erro interno no servidor."

    def post(self, request: Request) -> Response:
        """Inicia o fluxo de recuperação de senha.

        Valida o usuário e envia um e-mail contendo o link de redefinição.
        """
        serializer = EsqueciMinhaSenhaSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        username = serializer.validated_data["username"]

        try:
            logger.info("Fluxo de recuperação iniciado para %s", username)

            # 1. Busca usuário local
            user_local = User.objects.filter(username=username).first()

            # 2. Consulta SME
            dados_sme = self._consultar_sme(username, user_local)

            # 3. Valida existência do usuário
            self._validar_usuario_existe(user_local, dados_sme)

            # 4. Determina e valida o email
            email = self._obter_email(dados_sme, user_local, username)

            # 5. Sincroniza usuário local se necessário
            if dados_sme and dados_sme.get("nome"):
                user_local = self._criar_ou_atualizar_usuario_local(
                    username, dados_sme
                )

            # 6. Gera token e envia email
            return self._processar_envio_email(username, email)

        except EmailNaoCadastradoError as e:
            return Response({"detail": str(e)}, status=400)

        except UserNotFoundError as e:
            return Response({"detail": str(e)}, status=400)

        except Exception:
            logger.exception("Erro inesperado no fluxo de esqueci minha senha")
            return Response({"detail": self.MENSAGEM_ERRO_INTERNO}, status=500)

    def _consultar_sme(
        self, username: str, user_local: User | None
    ) -> dict | None:
        """
        Consulta dados do usuário na SME.
        Retorna None se houver erro e não existir usuário local.
        """
        try:
            return SmeIntegracaoService.informacao_usuario_sgp(username)
        except SmeIntegracaoError as e:
            logger.error("Erro ao consultar SME para %s: %s", username, str(e))
            if not user_local:
                raise UserNotFoundError(self.MENSAGEM_USUARIO_NAO_ENCONTRADO)
            return None
        except Exception:
            logger.exception(
                "Erro inesperado ao consultar SME para %s", username
            )
            if not user_local:
                raise UserNotFoundError(self.MENSAGEM_USUARIO_NAO_ENCONTRADO)
            return None

    def _validar_usuario_existe(
        self, user_local: User | None, dados_sme: dict | None
    ) -> None:
        """
        Valida se o usuário existe localmente ou na SME.
        """
        if not user_local and not dados_sme:
            raise UserNotFoundError(self.MENSAGEM_USUARIO_NAO_ENCONTRADO)

    def _obter_email(
        self, dados_sme: dict | None, user_local: User | None, username: str
    ) -> str:
        """
        Determina o email do usuário (prioridade: SME > banco local).
        Valida se o email existe e não está vazio.
        """
        email = None

        if dados_sme:
            email = dados_sme.get("email")

        if not email and user_local:
            email = getattr(user_local, "email", None)

        if not email or not email.strip():
            logger.warning("RF %s sem email cadastrado", username)
            raise EmailNaoCadastradoError(self.MENSAGEM_EMAIL_NAO_CADASTRADO)

        return email

    def _processar_envio_email(self, username: str, email: str) -> Response:
        """Gera token de recuperação e envia o e-mail para o usuário.

        Args:
            username (str): RF ou nome de usuário do usuário.
            email (str): Endereço de e-mail para envio.
        """
        logger.info("Gerando token: %s", username)

        token_data = SenhaService.gerar_token_para_reset(username, email)

        link_reset = f"{env('AMBIENTE_URL')}/recuperar-senha/{token_data['uid']}/{token_data['token']}"  # noqa: E501

        contexto = {
            "nome_usuario": token_data.get("name"),
            "link_reset": link_reset,
            "aplicacao_url": env("AMBIENTE_URL"),
        }

        EnviaEmailService.enviar(
            destinatario=email,
            assunto="Redefinição de senha",
            template_html="emails/reset_senha.html",
            contexto=contexto,
        )

        return Response(
            {
                "detail": f"Enviamos um link de recuperação para {anonimizar_email(email)}. <br/>"  # noqa: E501
                "Verifique sua caixa de entrada ou spam.",
            },
            status=200,
        )

    def _criar_ou_atualizar_usuario_local(
        self, username: str, dados_sme: dict
    ) -> User:
        """
        Cria ou atualiza usuário local com dados da SME.
        Usa update_or_create para evitar duplicação.
        """
        logger.info("Sincronizando usuário local para %s", username)

        nome = dados_sme.get("nome")
        if not nome:
            logger.warning(
                "Dados SME sem nome para %s, pulando sincronização", username
            )
            return User.objects.get(
                username=username
            )  # Retorna usuário existente

        try:
            with transaction.atomic():
                user, created = User.objects.update_or_create(
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

        except IntegrityError as e:
            logger.error(
                "Falha ao sincronizar usuário %s: %s", username, str(e)
            )
            raise EmailNaoCadastradoError(
                "Já existe um usuário com este e-mail. <br/>"
                "Entre em contato com o administrador do sistema."
            )


class RedefinirSenhaViewSet(APIView):
    """
    View para redefinição de senha via UID e token.

    Fonte da verdade:
    - A autenticação e alteração de senha acontecem na SME.
    - O banco local é atualizado como espelho (best-effort).

    Fluxo:
    1. Valida UID, token e senhas
    2. Redefine senha na SME (passo crítico)
    3. Tenta atualizar senha local (não crítico)
    4. Retorna sucesso ao usuário
    """

    permission_classes = [permissions.AllowAny]

    MENSAGEM_DADOS_INVALIDOS = "Dados inválidos."
    MENSAGEM_SUCESSO = "Senha redefinida com sucesso."
    STATUS_ERROR = "error"
    STATUS_SUCCESS = "success"

    def post(self, request: Request, *args, **kwargs) -> Response:
        """Processa a redefinição de senha usando UID e token.

        Valida os dados do formulário e redefine a senha na SME e localmente.
        """
        serializer = RedefinirSenhaSerializer(data=request.data)

        try:
            serializer.is_valid(raise_exception=True)
        except Exception:
            logger.warning(
                "Dados inválidos na redefinição de senha",
                extra={"errors": serializer.errors},
            )
            return Response(
                {
                    "status": self.STATUS_ERROR,
                    "detail": self.MENSAGEM_DADOS_INVALIDOS,
                    "errors": serializer.errors,
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        user = serializer.validated_data["user"]
        new_password = serializer.validated_data["new_pass"]

        logger.info(
            "Iniciando redefinição de senha para usuário ID=%s", user.id
        )

        try:
            SmeIntegracaoService.redefine_senha(
                user.username,
                new_password,
            )
        except SmeIntegracaoError as e:
            logger.error(
                "Falha ao redefinir senha na SME para usuário ID=%s: %s",
                user.id,
                str(e),
            )
            return Response(
                {
                    "status": self.STATUS_ERROR,
                    "detail": str(e),
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            with transaction.atomic():
                user.set_password(new_password)
                user.save(update_fields=["password"])
        except Exception:
            logger.exception(
                "Senha redefinida na SME, mas falha ao atualizar senha local "
                "para usuário ID=%s",
                user.id,
            )

        logger.info(
            "Fluxo de redefinição de senha concluído para usuário ID=%s",
            user.id,
        )

        return Response(
            {
                "status": self.STATUS_SUCCESS,
                "detail": self.MENSAGEM_SUCESSO,
            },
            status=status.HTTP_200_OK,
        )


class AtualizarSenhaViewSet(APIView):
    """View para alteração de senha de usuário autenticado.

    Recebe nova senha e atualiza tanto a SME quanto o banco local, quando
    possível.
    """

    permission_classes = [IsAuthenticated]

    MENSAGEM_SUCESSO = "Senha alterada com sucesso."
    MENSAGEM_ERRO_INTERNO = "Erro interno do servidor."

    def post(self, request: Request) -> Response:
        """Processa a alteração de senha do usuário autenticado.

        Valida a senha atual e atualiza a senha na SME e no banco local.
        """
        serializer = AtualizarSenhaSerializer(
            data=request.data, context={"request": request}
        )

        if not serializer.is_valid():
            logger.warning(f"Erro de validação: {serializer.errors}")
            return Response(
                serializer.errors, status=status.HTTP_400_BAD_REQUEST
            )

        user = request.user
        nova_senha = serializer.validated_data["nova_senha"]

        try:
            with transaction.atomic():
                SmeIntegracaoService.redefine_senha(user.username, nova_senha)

                user.set_password(nova_senha)
                user.save(update_fields=["password"])

                logger.info(
                    "Usuário ID %s alterou a senha com sucesso.", user.id
                )

                return Response(
                    {"detail": self.MENSAGEM_SUCESSO},
                    status=status.HTTP_200_OK,
                )

        except SmeIntegracaoError as e:
            logger.error(
                "Erro na integração SME para alteração de senha do usuário ID %s: %s",  # noqa: E501
                user.id,
                str(e),
            )
            return Response(
                {"detail": str(e)},
                status=status.HTTP_400_BAD_REQUEST,
            )

        except Exception:
            logger.exception(
                "Erro inesperado na alteração de senha do usuário ID: %s",
                user.id,
            )
            return Response(
                {"detail": self.MENSAGEM_ERRO_INTERNO},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )
