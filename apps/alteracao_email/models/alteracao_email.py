"""Modelo para representar solicitações de alteração de e-mail.

Este módulo define o modelo de dados que armazena o usuário, o novo e-mail,
seu token único de confirmação, a data de criação e se o token já foi usado.
"""

import uuid
from django.db import models
from django.conf import settings

class AlteracaoEmail(models.Model):
    """Representa uma solicitação de alteração de e-mail.

    A instância armazena o usuário que solicitou a alteração, o e-mail novo,
    o token único para validação, o timestamp de criação e se a solicitação
    já foi aplicada.
    """
    usuario = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    novo_email = models.EmailField()
    token = models.UUIDField(default=uuid.uuid4, unique=True)
    criado_em = models.DateTimeField(auto_now_add=True)
    ja_usado = models.BooleanField(default=False)

    def __str__(self):
        """Retorna representação textual da solicitação."""
        return f"{self.usuario.username} -> {self.novo_email}"