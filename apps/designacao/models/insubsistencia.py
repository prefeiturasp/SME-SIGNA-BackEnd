"""Modelo de insubsistências e seus tipos.

Define as insubsistências de designação ou cessação e regras de exclusão
lógica.
"""

from django.db import models
from django.utils import timezone


class TipoInsubsistencia(models.TextChoices):
    """Tipos de insubsistência válidos."""

    DESIGNACAO = "designacao"
    CESSACAO = "cessacao"


class Insubsistencia(models.Model):
    """Representa uma insubsistência vinculada a designação ou cessação."""

    designacao = models.ForeignKey(
        "Designacao",
        null=True,
        blank=True,
        on_delete=models.PROTECT,
        related_name="insubsistencia",
    )

    cessacao = models.ForeignKey(
        "Cessacao",
        null=True,
        blank=True,
        on_delete=models.PROTECT,
        related_name="insubsistencia",
    )

    numero_portaria = models.CharField(max_length=20)
    ano_vigente = models.CharField(max_length=6)
    sei_numero = models.CharField(max_length=30)

    doc = models.CharField(max_length=100, blank=True, default="")  # D.O
    observacoes = models.TextField(blank=True, default="")

    criado_em = models.DateTimeField(auto_now_add=True)
    is_deleted = models.BooleanField(default=False)
    deleted_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = "insubsistencia"

    def delete(
        self,
        using: str | None = None,
        keep_parents: bool = False,
    ) -> tuple[int, dict[str, int]]:
        """Realiza exclusão lógica da insubsistência.

        Marca o registro como removido sem excluí-lo fisicamente do banco,
        registrando a data e hora da exclusão.

        Args:
            using: Alias da conexão de banco de dados.
            keep_parents: Mantém os modelos pai na exclusão.

        """
        self.is_deleted = True
        self.deleted_at = timezone.now()
        self.save(update_fields=["is_deleted", "deleted_at"])

        return (1, {self._meta.label: 1})
