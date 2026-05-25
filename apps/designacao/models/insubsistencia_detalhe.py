from django.db import models
from apps.designacao.models.ato_administrativo import AtoAdministrativo


class InsubsistenciaDetalhe(models.Model):

    ato = models.OneToOneField(
        AtoAdministrativo, on_delete=models.CASCADE,
        related_name='insubsistencia_detalhe', primary_key=True
    )
    observacoes = models.TextField(blank=True, default='')

    class Meta:
        db_table = 'insubsistencia_detalhe'
