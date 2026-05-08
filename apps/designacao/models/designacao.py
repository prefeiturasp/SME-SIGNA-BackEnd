from django.db import models
from django.utils import timezone

class ImpedimentoSubstituicao(models.Model):
    codigo = models.CharField(max_length=50, unique=True)
    descricao = models.CharField(max_length=255)

    class Meta:
        db_table = 'impedimento_substituicao'

    def __str__(self):
        return self.descricao
    
class Designacao(models.Model):

    class TipoVaga(models.TextChoices):
        VAGO = 'VAGO', 'Cargo Vago'
        DISPONIVEL = 'DISPONIVEL', 'Cargo Disponível'

    class CargoVaga(models.IntegerChoices):
        ASSISTENTE_DIRETOR = 3085, "ASSISTENTE DE DIRETOR DE ESCOLA"
        DIRETOR = 3360, "DIRETOR DE ESCOLA"
        COORDENADOR_PEDAGOGICO = 3379, "COORDENADOR PEDAGOGICO"
        SECRETARIO = 3182, "SECRETARIO DE ESCOLA"
        SUPERVISOR = 3352, "SUPERVISOR ESCOLAR"

    # --- Unidade ---
    dre_nome = models.CharField(max_length=255)
    unidade_proponente = models.CharField(max_length=255)
    codigo_hierarquico = models.CharField(max_length=50)


    # --- Indicado ---
    indicado_nome_civil = models.CharField(max_length=255, blank=True, default="")
    indicado_nome_servidor = models.CharField(max_length=255)
    indicado_rf = models.CharField(max_length=8)
    indicado_vinculo = models.IntegerField()
    indicado_cargo_base = models.CharField(max_length=255)
    indicado_codigo_cargo_base = models.IntegerField(null=True, blank=True)
    indicado_lotacao = models.CharField(max_length=255)
    indicado_cargo_sobreposto = models.CharField(max_length=255, blank=True, default="")
    indicado_codigo_cargo_sobreposto = models.IntegerField(null=True, blank=True)
    indicado_local_exercicio = models.CharField(max_length=255)
    indicado_local_servico = models.CharField(max_length=255, blank=True, default="")

    # --- Titular ---
    titular_nome_civil = models.CharField(max_length=255, blank=True, default="")
    titular_nome_servidor = models.CharField(max_length=255, blank=True, default="")
    titular_rf = models.CharField(max_length=8, blank=True, default="")
    titular_vinculo = models.IntegerField(null=True, blank=True)
    titular_cargo_base = models.CharField(max_length=255, blank=True, default="")
    titular_codigo_cargo_base = models.IntegerField(null=True, blank=True)
    titular_lotacao = models.CharField(max_length=255, blank=True, default="")
    titular_cargo_sobreposto = models.CharField(max_length=255, blank=True, default="")
    titular_codigo_cargo_sobreposto = models.IntegerField(null=True, blank=True)
    titular_local_exercicio = models.CharField(max_length=255, blank=True, default="")
    titular_local_servico = models.CharField(max_length=255, blank=True, default="")

    # --- Portaria ---
    numero_portaria = models.CharField(max_length=20)
    ano_vigente = models.CharField(max_length=6)
    sei_numero = models.CharField(max_length=30)
    doc = models.CharField(max_length=100, blank=True, default="")#Campo D.O
    data_inicio = models.DateField()
    data_fim = models.DateField(null=True, blank=True)
    carater_excepcional = models.BooleanField(default=False)
    impedimento_substituicao = models.ForeignKey(
        ImpedimentoSubstituicao,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='designacoes'
    )
    com_afastamento = models.BooleanField(default=False)
    possui_pendencia = models.BooleanField(default=False)
    pendencias = models.TextField(blank=True, default="")
    motivo_afastamento = models.TextField(blank=True, default="")

    # --- Informações Adicionais --- 
    informacoes_adicionais = models.TextField(blank=True, default="")
    detalhe_para_quadro_de_historico_por_ano = models.BooleanField(default=True)

    # --- Vaga ---
    tipo_vaga = models.CharField(max_length=15, choices=TipoVaga.choices)
    cargo_vaga = models.IntegerField(choices=CargoVaga.choices, null=True, blank=True)

    # --- Controle ---
    criado_em = models.DateTimeField(auto_now_add=True)
    is_deleted = models.BooleanField(default=False)
    deleted_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = 'designacao'


    @classmethod
    def get_cargos_formatados(cls):
        """Substitui a constante CARGOS_GESTAO_ESCOLAR"""
        return [
            {"codigoCargo": choice.value, "nomeCargo": choice.label}
            for choice in cls.CargoVaga
        ]
    

    def delete(self, *args, **kwargs):
        self.is_deleted = True
        self.deleted_at = timezone.now()
        self.save()
