from django.db import models
from django.utils import timezone


class Cessacao(models.Model):

    designacao = models.OneToOneField(
        'Designacao',
        on_delete=models.CASCADE,
        related_name='cessacao'
    )

    numero_portaria = models.CharField(max_length=20)
    ano_vigente = models.CharField(max_length=6)
    sei_numero = models.CharField(max_length=30)

    a_pedido = models.BooleanField(default=False)
    remocao = models.BooleanField(default=False)
    aposentadoria = models.BooleanField(default=False)
    data_designacao = models.DateField()
    doc = models.CharField(  # D.O
        max_length=100,
        blank=True,
        default=""
    )

    criado_em = models.DateTimeField(auto_now_add=True)
    is_deleted = models.BooleanField(default=False)
    deleted_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = 'cessacao'

    def delete(self, *args, **kwargs):
        self.is_deleted = True
        self.deleted_at = timezone.now()
        self.save()