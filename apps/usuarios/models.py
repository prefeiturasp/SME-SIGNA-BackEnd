import uuid
from django.db import models
from django.contrib.auth.models import AbstractUser

class User(AbstractUser):
    """
    Modelo de usuário customizado básico para JWT e futuras expansões.
    """
    uuid = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    name = models.CharField("Nome completo", max_length=150, blank=True)
    cpf = models.CharField("CPF", max_length=11, unique=True, null=True, blank=True)
    email = models.EmailField("E-mail", unique=True, null=True, blank=True)

    class Meta:
        verbose_name = "Usuário"
        verbose_name_plural = "Usuários"

    def __str__(self):
        return self.username or self.email or str(self.uuid)

    def save(self, *args, **kwargs):
        """
        Sobrescreve o método save para garantir que a senha seja criptografada
        quando o usuário é criado via seed, script ou API personalizada.
        """
        if self.password and not self.password.startswith(('pbkdf2_', 'bcrypt', 'argon2')):
            self.set_password(self.password)

        super().save(*args, **kwargs)
