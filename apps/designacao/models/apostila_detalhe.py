from django.db import models
from apps.designacao.models.ato_administrativo import AtoAdministrativo


class ApostilaDetalhe(models.Model):

    ato = models.OneToOneField(
        AtoAdministrativo,
        on_delete=models.CASCADE,
        related_name="apostila_detalhe",
        primary_key=True,
    )
    observacao = models.TextField()

    class Meta:
        db_table = "apostila_detalhe"


class ApostilaAlteracao(models.Model):

    apostila = models.ForeignKey(
        ApostilaDetalhe, on_delete=models.CASCADE, related_name="alteracoes"
    )
    campo_alterado = models.CharField(max_length=100)
    valor_anterior = models.TextField()
    valor_novo = models.TextField()

    class Meta:
        db_table = "apostila_alteracao"
        constraints = [
            models.UniqueConstraint(
                fields=["apostila", "campo_alterado"], name="unique_campo_por_apostila"
            )
        ]
