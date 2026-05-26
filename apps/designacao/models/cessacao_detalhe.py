"""Modelo de detalhes específicos de cessação.

Armazena informações complementares associadas a um ato de cessação.
"""

from django.db import models
from apps.designacao.models.ato_administrativo import AtoAdministrativo


class CessacaoDetalhe(models.Model):
    """Detalhes de uma cessação vinculada a um ato administrativo."""

    ato = models.OneToOneField(
        AtoAdministrativo, on_delete=models.CASCADE,
        related_name='cessacao_detalhe', primary_key=True
    )

    a_pedido      = models.BooleanField(default=False)
    remocao       = models.BooleanField(default=False)
    aposentadoria = models.BooleanField(default=False)
    data_cessacao = models.DateField()

    class Meta:
        db_table = 'cessacao_detalhe'
