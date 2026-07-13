"""Modelo de detalhes específicos de anulação de apostila.

Armazena informações complementares de uma insubsistência cujo ato pai
é uma apostila, registrando o texto formal da anulação.
"""

from django.db import models

from apps.designacao.models.ato_administrativo import AtoAdministrativo


class InsubsistenciaApostilaDetalhe(models.Model):
    """Detalhes de anulação de apostila vinculados a um ato de insubsistência."""  # noqa: E501

    ato = models.OneToOneField(
        AtoAdministrativo,
        on_delete=models.CASCADE,
        related_name="insubsistencia_apostila_detalhe",
        primary_key=True,
    )
    texto = models.TextField(blank=True, default="")

    class Meta:
        db_table = "insubsistencia_apostila_detalhe"
