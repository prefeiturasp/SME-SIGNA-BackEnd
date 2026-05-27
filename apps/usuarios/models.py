"""Modelos do app de usuários.

Contém o modelo de usuário customizado que estende o AbstractUser
com campos adicionais e comportamento de senha seguro.
"""

import uuid

from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):
    """Modelo de usuário customizado.

    Estende o AbstractUser com UUID, nome completo, CPF e e-mail opcional.
    """

    uuid = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    name = models.CharField("Nome completo", max_length=150, blank=True)
    cpf = models.CharField(
        "CPF", max_length=11, unique=True, null=True, blank=True
    )
    email = models.EmailField("E-mail", unique=True, null=True, blank=True)

    class Meta:
        verbose_name = "Usuário"
        verbose_name_plural = "Usuários"

    def __str__(self):
        """Retorna a representação em string do usuário.

        Prioriza username, depois e-mail e, por fim, UUID.
        """
        return self.username or self.email or str(self.uuid)

    def save(self, *args, **kwargs):
        """Sobrescreve o método save para garantir a criptografia da senha.

        Se a senha fornecida não estiver em formato hash suportado, ela é
        convertida usando set_password antes da persistência.
        """
        if self.password and not self.password.startswith(
            ("pbkdf2_", "bcrypt", "argon2")
        ):
            self.set_password(self.password)

        super().save(*args, **kwargs)
