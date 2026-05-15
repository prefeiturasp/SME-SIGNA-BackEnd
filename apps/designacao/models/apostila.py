from django.core.exceptions import ValidationError
from django.db import models


class Apostila(models.Model):

    class Tipo(models.TextChoices):
        APOSTILA = "APOSTILA", "Apostila"
        ANULACAO = "ANULACAO", "Anulação de Apostila"

    tipo = models.CharField(max_length=20, choices=Tipo.choices)

    designacao = models.ForeignKey(
        "Designacao",
        null=True,
        blank=True,
        on_delete=models.PROTECT,
        related_name="apostilas",
    )

    cessacao = models.ForeignKey(
        "Cessacao",
        null=True,
        blank=True,
        on_delete=models.PROTECT,
        related_name="apostilas",
    )

    apostila_referencia = models.ForeignKey(
        "self",
        null=True,
        blank=True,
        on_delete=models.PROTECT,
        related_name="anulacoes",
    )

    sei_numero = models.CharField(max_length=30)

    d_o = models.CharField(max_length=100, blank=True, default="")  # D.O

    observacao = models.TextField()

    criado_em = models.DateTimeField(auto_now_add=True)

    is_deleted = models.BooleanField(default=False)

    class Meta:
        db_table = "apostila"

    def clean(self):

        if sum([bool(self.designacao), bool(self.cessacao)]) != 1:
            raise ValidationError(
                "A apostila deve estar vinculada a uma designação OU cessação."
            )

        if self.tipo == self.Tipo.ANULACAO and not self.apostila_referencia:
            raise ValidationError("Anulação deve referenciar uma apostila.")

        if self.tipo == self.Tipo.APOSTILA and self.apostila_referencia:
            raise ValidationError("Apostila não pode ter referência.")
