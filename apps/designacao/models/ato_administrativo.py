from django.core.exceptions import ValidationError
from django.db import models


class AtoAdministrativo(models.Model):

    class Tipo(models.TextChoices):
        DESIGNACAO     = 'DESIGNACAO',     'Designação'
        CESSACAO       = 'CESSACAO',       'Cessação'
        APOSTILA       = 'APOSTILA',       'Apostila'
        INSUBSISTENCIA = 'INSUBSISTENCIA', 'Insubsistência'

    _TIPOS_PAI_VALIDOS = {
        'CESSACAO':       {'DESIGNACAO'},
        'APOSTILA':       {'DESIGNACAO', 'CESSACAO'},
        'INSUBSISTENCIA': {'DESIGNACAO', 'CESSACAO', 'APOSTILA', 'INSUBSISTENCIA'},
    }

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

    ativo     = models.BooleanField(default=True)
    criado_em = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'ato_administrativo'

    def clean(self):
        if self.ato_pai_id:
            tipos_validos = self._TIPOS_PAI_VALIDOS.get(self.tipo, set())
            if self.ato_pai.tipo not in tipos_validos:
                raise ValidationError(
                    f'{self.tipo} não pode ter {self.ato_pai.tipo} como ato pai.'
                )
        elif self.tipo != self.Tipo.DESIGNACAO:
            raise ValidationError(f'{self.tipo} precisa de um ato pai.')

        # Uma designação só pode ter uma cessação ativa por vez
        if self.tipo == self.Tipo.CESSACAO and self.ato_pai_id:
            qs = AtoAdministrativo.objects.filter(
                tipo=self.Tipo.CESSACAO,
                ato_pai_id=self.ato_pai_id,
                ativo=True,
            )
            if self.pk:
                qs = qs.exclude(pk=self.pk)
            if qs.exists():
                raise ValidationError(
                    {'ato_pai': 'Esta designação já possui uma cessação ativa.'}
                )

    def save(self, *args, **kwargs):
        if self.ato_pai_id and not self.ato_raiz_id:
            pai = self.ato_pai
            self.ato_raiz_id = pai.ato_raiz_id if pai.ato_raiz_id else pai.pk
        if not kwargs.get('update_fields'):
            self.full_clean()
        super().save(*args, **kwargs)

    @property
    def status(self):
        if not self.ativo:
            return 'insubsistente'
        if self.tipo == self.Tipo.DESIGNACAO:
            tem_cessacao_ativa = any(
                f.tipo == self.Tipo.CESSACAO and f.ativo
                for f in self.filhos.all()
            )
            if tem_cessacao_ativa:
                return 'cessada'
        return 'ativo'

    @property
    def eh_valido(self):
        return self.ativo
