"""Modelo de cessação de designação.

Registra os dados de cessação de uma designação, incluindo tipo,
portaria e data da decisão.
"""

from django.db import models
from django.utils import timezone


class Cessacao(models.Model):
    """Representa a cessação de uma designação."""

    designacao = models.OneToOneField(
        "Designacao", on_delete=models.PROTECT, related_name="cessacao"
    )

    numero_portaria = models.CharField(max_length=20)
    ano_vigente = models.CharField(max_length=6)
    sei_numero = models.CharField(max_length=30)

    a_pedido = models.BooleanField(default=False)
    remocao = models.BooleanField(default=False)
    aposentadoria = models.BooleanField(default=False)
    data_designacao = models.DateField()
    doc = models.CharField(max_length=100, blank=True, default="")  # D.O

    criado_em = models.DateTimeField(auto_now_add=True)
    is_deleted = models.BooleanField(default=False)
    deleted_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = "cessacao"

    def delete(
        self,
        using: str | None = None,
        keep_parents: bool = False,
    ) -> tuple[int, dict[str, int]]:
        """Realiza exclusão lógica da cessação.

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
