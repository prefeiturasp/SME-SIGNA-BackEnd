import environ
import logging

from django.db import transaction

from django.contrib.auth import get_user_model

from rest_framework import status, permissions
from rest_framework.views import APIView
from rest_framework.permissions import AllowAny
from rest_framework.response import Response

from apps.helpers.utils import anonimizar_email
from apps.usuarios.api.serializers.senha_serializer import EsqueciMinhaSenhaSerializer, RedefinirSenhaSerializer
from apps.helpers.exceptions import EmailNaoCadastrado, UserNotFoundError, SmeIntegracaoException
from apps.usuarios.services.senha_service import SenhaService
from apps.usuarios.services.sme_integracao_service import SmeIntegracaoService
from apps.usuarios.services.envia_email_service import EnviaEmailService

logger = logging.getLogger(__name__)
User = get_user_model()
env = environ.Env()


class EsqueciMinhaSenhaViewSet(APIView):
    permission_classes = [AllowAny]

    MENSAGEM_EMAIL_NAO_CADASTRADO = (
        "E-mail não encontrado! <br/>"
        "Para resolver este problema, entre em contato com o administrador do sistema."
    )

    def post(self, request):
        serializer = EsqueciMinhaSenhaSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        username = serializer.validated_data["username"]

        try:
            logger.info("Fluxo de recuperação iniciado")

            # 1. Verifica usuário local
            user_local = User.objects.filter(username=username).first()
            if not user_local:
                logger.warning("RF %s não encontrado no banco local", username)
                raise UserNotFoundError("Usuário não encontrado")

            # 2. Consulta API coreSSO
            try:
                result = SmeIntegracaoService.informacao_usuario_sgp(username)
                email = result.get("email")
            except Exception:
                logger.warning("Falha ao consultar API externa para RF %s", username)
                email = None

            # 3. Se API não retornou email → tenta usar banco local
            if not email:
                email = getattr(user_local, "email", None)

            # 4. Ainda sem email → erro
            if not email:
                logger.warning("RF %s sem email cadastrado em nenhum lugar", username)
                raise EmailNaoCadastrado(self.MENSAGEM_EMAIL_NAO_CADASTRADO)

            # 5. gerar token + enviar email
            return self._processar_envio_email(username, email)

        except EmailNaoCadastrado as e:
            return Response({"detail": str(e)}, status=400)

        except UserNotFoundError as e:
            return Response({"detail": str(e)}, status=404)

        except Exception:
            logger.exception("Erro inesperado no fluxo de esqueci minha senha")
            return Response({"detail": "Erro interno no servidor."}, status=500)

    def _processar_envio_email(self, username, email):
        logger.info("Gerando token: %s", username)

        token_data = SenhaService.gerar_token_para_reset(username, email)

        link_reset = f"{env('AMBIENTE_URL')}/recuperar-senha/{token_data['uid']}/{token_data['token']}"

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
                "detail": f"Enviamos um link de recuperação para {anonimizar_email(email)}. <br/>"
                          "Verifique sua caixa de entrada ou spam.",
            },
            status=200,
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

    def post(self, request, *args, **kwargs):
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
                    "status": "error",
                    "detail": "Dados inválidos.",
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
        except SmeIntegracaoException as e:
            logger.error(
                "Falha ao redefinir senha na SME para usuário ID=%s: %s",
                user.id,
                str(e),
            )
            return Response(
                {
                    "status": "error",
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
                "status": "success",
                "detail": "Senha redefinida com sucesso.",
            },
            status=status.HTTP_200_OK,
        )
