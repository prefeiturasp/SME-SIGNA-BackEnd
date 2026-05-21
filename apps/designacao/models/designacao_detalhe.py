from django.db import models

from apps.designacao.models.ato_administrativo import AtoAdministrativo
from apps.designacao.models.designacao import ImpedimentoSubstituicao


class DesignacaoDetalhe(models.Model):

    class TipoVaga(models.TextChoices):
        VAGO = "VAGO", "Cargo Vago"
        DISPONIVEL = "DISPONIVEL", "Cargo Disponível"

    class CargoVaga(models.IntegerChoices):
        ASSISTENTE_DIRETOR = 3085, "ASSISTENTE DE DIRETOR DE ESCOLA"
        DIRETOR = 3360, "DIRETOR DE ESCOLA"
        COORDENADOR_PEDAGOGICO = 3379, "COORDENADOR PEDAGOGICO"
        SECRETARIO = 3182, "SECRETARIO DE ESCOLA"
        SUPERVISOR = 3352, "SUPERVISOR ESCOLAR"

    ato = models.OneToOneField(
        AtoAdministrativo,
        on_delete=models.CASCADE,
        related_name="designacao_detalhe",
        primary_key=True,
    )

    # Unidade
    dre_nome = models.CharField(max_length=255)
    unidade_proponente = models.CharField(max_length=255)
    codigo_hierarquico = models.CharField(max_length=50)
    ue = models.CharField(max_length=50, blank=True, default="")
    dre = models.CharField(max_length=50, blank=True, default="")
    funcionarios_da_unidade = models.CharField(
        max_length=50, blank=True, default=""
    )

    # Indicado
    indicado_nome_civil = models.CharField(
        max_length=255, blank=True, default=""
    )
    indicado_nome_servidor = models.CharField(max_length=255)
    indicado_rf = models.CharField(max_length=8)
    indicado_vinculo = models.IntegerField()
    indicado_cargo_base = models.CharField(max_length=255)
    indicado_codigo_cargo_base = models.IntegerField(null=True, blank=True)
    indicado_lotacao = models.CharField(max_length=255)
    indicado_cargo_sobreposto = models.CharField(
        max_length=255, blank=True, default=""
    )
    indicado_codigo_cargo_sobreposto = models.IntegerField(
        null=True, blank=True
    )
    indicado_local_exercicio = models.CharField(max_length=255)
    indicado_local_servico = models.CharField(
        max_length=255, blank=True, default=""
    )

    # Titular
    titular_nome_civil = models.CharField(
        max_length=255, blank=True, default=""
    )
    titular_nome_servidor = models.CharField(
        max_length=255, blank=True, default=""
    )
    titular_rf = models.CharField(max_length=8, blank=True, default="")
    titular_vinculo = models.IntegerField(null=True, blank=True)
    titular_cargo_base = models.CharField(
        max_length=255, blank=True, default=""
    )
    titular_codigo_cargo_base = models.IntegerField(null=True, blank=True)
    titular_lotacao = models.CharField(max_length=255, blank=True, default="")
    titular_cargo_sobreposto = models.CharField(
        max_length=255, blank=True, default=""
    )
    titular_codigo_cargo_sobreposto = models.IntegerField(
        null=True, blank=True
    )
    titular_local_exercicio = models.CharField(
        max_length=255, blank=True, default=""
    )
    titular_local_servico = models.CharField(
        max_length=255, blank=True, default=""
    )

    # Período
    data_inicio = models.DateField()
    data_fim = models.DateField(null=True, blank=True)

    # Flags
    carater_excepcional = models.BooleanField(default=False)
    com_afastamento = models.BooleanField(default=False)
    possui_pendencia = models.BooleanField(default=False)
    pendencias = models.TextField(blank=True, default="")
    motivo_afastamento = models.TextField(blank=True, default="")
    informacoes_adicionais = models.TextField(blank=True, default="")
    detalhe_para_quadro_de_historico_por_ano = models.BooleanField(
        default=True
    )

    impedimento_substituicao = models.ForeignKey(
        ImpedimentoSubstituicao,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="designacoes_detalhe",
    )

    tipo_vaga = models.CharField(max_length=15, choices=TipoVaga.choices)
    cargo_vaga = models.IntegerField(
        choices=CargoVaga.choices, null=True, blank=True
    )

    class Meta:
        db_table = "designacao_detalhe"

    @classmethod
    def get_cargos_formatados(cls):
        return [
            {"codigoCargo": c.value, "nomeCargo": c.label}
            for c in cls.CargoVaga
        ]
