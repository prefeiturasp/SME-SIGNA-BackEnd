"""Testes para o serviço de envio de e-mail.

Este módulo valida o comportamento do serviço de envio de e-mails,
incluindo envio bem-sucedido, validação de parâmetros obrigatórios e
tratamento de exceções inesperadas.
"""

from unittest.mock import patch

import pytest

from django.core import mail
from django.core.exceptions import ValidationError

from apps.usuarios.services.envia_email_service import EnviaEmailService


@pytest.fixture(autouse=True)
def use_locmem_email_backend(settings):
    """Configura o backend de e-mail para testes.

    O backend em memória evita envios reais de e-mail durante a execução dos
    testes.
    """
    settings.EMAIL_BACKEND = "django.core.mail.backends.locmem.EmailBackend"


@pytest.mark.django_db
class TestEnviaEmailService:
    """Testa o serviço de envio de e-mail.

    Verifica envio de e-mail com sucesso e as validações de dados obrigatórios.
    """

    @pytest.fixture
    def email_data(self):
        """Retorna dados válidos de e-mail para os testes."""
        return {
            "destinatario": "test@example.com",
            "assunto": "Teste de envio",
            "template_html": "emails/exemplo.html",
            "contexto": {"nome": "Usuário Teste"},
        }

    def test_send_email_success(self, email_data):
        """Verifica que um e-mail é enviado com os dados esperados."""
        mail.outbox = []

        EnviaEmailService.enviar(**email_data)

        assert len(mail.outbox) == 1
        email = mail.outbox[0]
        assert email.subject == email_data["assunto"]
        assert email.to == [email_data["destinatario"]]
        assert "Usuário Teste" in email.body

    def test_send_email_empty_destinatario_raises(self, email_data):
        """Verifica que destinatário vazio causa ValidationError."""
        email_data["destinatario"] = ""
        with pytest.raises(ValidationError):
            EnviaEmailService.enviar(**email_data)

    def test_send_email_empty_assunto_raises(self, email_data):
        """Verifica que assunto vazio causa ValidationError."""
        email_data["assunto"] = ""
        with pytest.raises(ValidationError):
            EnviaEmailService.enviar(**email_data)

    def test_send_email_unexpected_exception_raises_runtimeerror(self, email_data):
        """Verifica que exceções inesperadas são convertidas em RuntimeError."""
        with patch(
            "django.core.mail.EmailMessage.send",
            side_effect=Exception("Erro inesperado"),
        ):
            with pytest.raises(RuntimeError, match="Erro inesperado ao enviar e-mail."):
                EnviaEmailService.enviar(**email_data)
