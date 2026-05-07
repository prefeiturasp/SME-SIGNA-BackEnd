from django.db import models


class AtoAdministrativo(models.Model):

    class Tipo(models.TextChoices):
        DESIGNACAO     = 'DESIGNACAO',     'Designação'
        CESSACAO       = 'CESSACAO',       'Cessação'
        APOSTILA       = 'APOSTILA',       'Apostila'
        INSUBSISTENCIA = 'INSUBSISTENCIA', 'Insubsistência'

    tipo = models.CharField(max_length=20, choices=Tipo.choices)

    ato_pai = models.ForeignKey(
        'self', null=True, blank=True,
        on_delete=models.PROTECT, related_name='filhos'
    )
    ato_raiz = models.ForeignKey(
        'self', null=True, blank=True,
        on_delete=models.PROTECT, related_name='descendentes'
    )

    # Apostila não usa numero_portaria/ano_vigente — ficam blank para esse tipo
    numero_portaria = models.CharField(max_length=20, blank=True, default='')
    ano_vigente     = models.CharField(max_length=6,  blank=True, default='')
    sei_numero      = models.CharField(max_length=30)
    doc             = models.CharField(max_length=100, blank=True, default='')

    criado_em = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'ato_administrativo'
        constraints = [
            models.UniqueConstraint(
                fields=['ato_pai'],
                condition=models.Q(tipo='CESSACAO'),
                name='unique_cessacao_por_ato_pai'
            )
        ]

    def save(self, *args, **kwargs):
        if self.ato_pai_id and not self.ato_raiz_id:
            pai = self.ato_pai
            self.ato_raiz_id = pai.ato_raiz_id if pai.ato_raiz_id else pai.pk
        super().save(*args, **kwargs)

    @property
    def status(self):
        for filho in self.filhos.filter(tipo=AtoAdministrativo.Tipo.INSUBSISTENCIA):
            if filho.status == 'ativo':
                return 'insubsistente'
        if self.ato_pai_id and self.ato_pai.status == 'insubsistente':
            return 'invalido'
        return 'ativo'

    @property
    def eh_valido(self):
        return self.status == 'ativo'
