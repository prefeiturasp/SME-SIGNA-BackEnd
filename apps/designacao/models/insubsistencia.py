from django.db import models
from django.utils import timezone


class TipoInsubsistencia(models.TextChoices):
    DESIGNACAO = "designacao"
    CESSACAO = "cessacao"


class Insubsistencia(models.Model):

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

    def delete(self, *args, **kwargs):
        self.is_deleted = True
        self.deleted_at = timezone.now()
        self.save()
