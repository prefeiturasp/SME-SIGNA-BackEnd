"""Serviço de envio de e-mails HTML para o app de usuários.

Fornece validação básica de parâmetros e envio de mensagens usando
as ferramentas de e-mail do Django.
"""

import logging

from django.core.exceptions import ValidationError
from django.core.mail import BadHeaderError, EmailMessage
from django.template.loader import render_to_string

logger = logging.getLogger(__name__)


class EnviaEmailService:
    """Serviço para envio de e-mails HTML usando recursos padrão do Django."""

    @staticmethod
    def validar(destinatario, assunto):
        """Valida os parâmetros básicos do e-mail.

        Args:
            destinatario (str|list): Destinatário ou lista de destinatários.
            assunto (str): Assunto da mensagem.

        Raises:
            ValidationError: Quando destinatário ou assunto não são fornecidos.
        """
        if not destinatario:
            raise ValidationError("Destinatário não pode ser vazio.")
        if not assunto:
            raise ValidationError("Assunto não pode ser vazio.")

    @staticmethod
    def renderizar_corpo(template_html, contexto):
        """Renderiza o corpo do e-mail a partir de um template HTML.

        Args:
            template_html (str): Caminho para o template HTML.
            contexto (dict): Contexto usado na renderização do template.

        Returns:
            str: Corpo do e-mail renderizado em HTML.
        """
        return render_to_string(template_html, contexto)

    @classmethod
    def enviar(cls, destinatario, assunto, template_html, contexto):
        """Envia um e-mail HTML.

        Args:
            destinatario (str|list): Endereço ou lista de endereços de destino.
            assunto (str): Assunto do e-mail.
            template_html (str): Template HTML para o corpo do e-mail.
            contexto (dict): Contexto para renderizar o template.

        Raises:
            ValidationError: Se destinatário ou assunto estiverem ausentes.
            BadHeaderError: Se o cabeçalho do e-mail estiver inválido.
            RuntimeError: Em caso de erro inesperado no envio.
        """

        try:
            cls.validar(destinatario, assunto)

            corpo_html = cls.renderizar_corpo(template_html, contexto)

            email = EmailMessage(
                subject=assunto,
                body=corpo_html,
                to=(
                    [destinatario]
                    if isinstance(destinatario, str)
                    else destinatario
                ),
            )
            email.content_subtype = "html"
            email.send()

            logger.info(
                f"E-mail enviado com sucesso para {destinatario} usando o template '{template_html}'."  # noqa: E501
            )

        except (ValidationError, BadHeaderError) as e:
            logger.error(f"Erro ao enviar e-mail: {str(e)}")
            raise

        except Exception as e:
            logger.exception("Erro inesperado ao enviar e-mail.")
            raise RuntimeError("Erro inesperado ao enviar e-mail.") from e
