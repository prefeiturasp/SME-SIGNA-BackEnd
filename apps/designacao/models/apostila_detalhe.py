"""Modelos de detalhes e alterações de apostila.

Define a estrutura de dados para armazenar informações de apostila e
suas alterações históricas associadas a atos administrativos.
"""

from django.db import models
from apps.designacao.models.ato_administrativo import AtoAdministrativo


class ApostilaDetalhe(models.Model):
    """Detalhes de apostila vinculados a um ato administrativo."""

    ato = models.OneToOneField(
        AtoAdministrativo, on_delete=models.CASCADE,
        related_name='apostila_detalhe', primary_key=True
    )
    observacao = models.TextField()

    class Meta:
        db_table = 'apostila_detalhe'


class ApostilaAlteracao(models.Model):
    """Registra alterações feitas em campos de uma apostila."""

    apostila       = models.ForeignKey(ApostilaDetalhe, on_delete=models.CASCADE, related_name='alteracoes')
    campo_alterado = models.CharField(max_length=100)
    valor_anterior = models.TextField()
    valor_novo     = models.TextField()

    class Meta:
        db_table = 'apostila_alteracao'
        constraints = [
            models.UniqueConstraint(
                fields=['apostila', 'campo_alterado'],
                name='unique_campo_por_apostila'
            )
        ]
