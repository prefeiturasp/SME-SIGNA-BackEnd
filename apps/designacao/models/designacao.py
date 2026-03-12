from django.db import models
from datetime import datetime

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

    class ImpedimentoSubstituicao(models.TextChoices):
        LICENCA_GESTANTE = 'LIC_GESTANTE', 'Por licença gestante'
        LICENCA_MEDICA = 'LIC_MEDICA', 'Por licença médica'
        LICENCA_PATERNIDADE = 'LIC_PATERNIDADE', 'Por licença paternidade'
        FERIAS = 'FERIAS', 'Por férias'
        LICENCA_MAT_ESP = 'LIC_MAT_ESP', 'Por licença maternidade especial'
        LICENCA_ADOCAO = 'LIC_ADOCAO', 'Por licença adoção'
        LICENCA_GUARDA = 'LIC_GUARDA', 'Por licença guarda de menor'
        MANDATO_ELETIVO = 'MANDATO_ELETIVO', 'Para concorrer a mandato eletivo (Portaria 20/SEGES/2024)'
        LICENCA_NOJO = 'LIC_NOJO', 'Por licença nojo'
        LICENCA_GALA = 'LIC_GALA', 'Por licença gala'
        AFAST_CURSOS = 'AFAST_CURSOS', 'Por afastamento Por Cursos/Congressos/Competições'
        LICENCA_MATERNIDADE = 'LIC_MATERNIDADE', 'Por licença maternidade'
        PRORROG_GESTANTE = 'PRORROG_GESTANTE', 'Por prorrogação da licença à gestante'
        PARENTAL_CURTA = 'PARENTAL_CURTA', 'Por licença parental de curta duração'
        PARENTAL_LONGA = 'PARENTAL_LONGA', 'Por licença parental de longa duração'
        EVENTO_REUNIAO = 'EVENTO_REUNIAO', 'Por Evento/Reunião'
        READAPT_FUNC = 'READAPT_FUNC', 'Por readaptação funcional (Art. 39 Lei 8.979/79)'
        SERV_TEC_A = 'SERV_TEC_A', 'Para prestar serviços técnico-educacionais (Art. 66, IX, a)'
        CARGO_COMISSAO = 'CARGO_COMISSAO', 'Por exercer cargos em comissão (Art. 45 Lei 8.989/79)'
        SERV_TEC_B = 'SERV_TEC_B', 'Para prestar serviços técnico-educacionais (Art. 66, IX, b)'
        TRANSF_TEMP = 'TRANSF_TEMP', 'Por transferência temporária (Decreto 57.444/16)'
        DIRIGENTE_SINDICAL = 'DIRIGENTE_SINDICAL', 'Por exercer mandato de dirigente sindical'
        AFAST_EXCEP = 'AFAST_EXCEP', 'Pelo afastamento excepcional (Art. 66, IX, b)'

    # --- Unidade ---
    dre_nome = models.CharField(max_length=255)
    unidade_proponente = models.CharField(max_length=255)
    codigo_hierarquico = models.CharField(max_length=50)

    # --- Indicado ---
    indicado_nome_civil = models.CharField(max_length=255)
    indicado_nome_servidor = models.CharField(max_length=255)
    indicado_rf = models.CharField(max_length=8)
    indicado_vinculo = models.IntegerField()
    indicado_cargo_base = models.CharField(max_length=255)
    indicado_lotacao = models.CharField(max_length=255)
    indicado_cargo_sobreposto = models.CharField(max_length=255, blank=True, default="")
    indicado_local_exercicio = models.CharField(max_length=255)
    indicado_local_servico = models.CharField(max_length=255, blank=True, default="")

    # --- Titular ---
    titular_nome_civil = models.CharField(max_length=255, blank=True, default="")
    titular_nome_servidor = models.CharField(max_length=255, blank=True, default="")
    titular_rf = models.CharField(max_length=8, blank=True, default="")
    titular_vinculo = models.IntegerField(null=True, blank=True)
    titular_cargo_base = models.CharField(max_length=255, blank=True, default="")
    titular_lotacao = models.CharField(max_length=255, blank=True, default="")
    titular_cargo_sobreposto = models.CharField(max_length=255, blank=True, default="")
    titular_local_exercicio = models.CharField(max_length=255, blank=True, default="")
    titular_local_servico = models.CharField(max_length=255, blank=True, default="")

    # --- Portaria ---
    numero_portaria = models.CharField(max_length=20)
    ano_vigente = models.CharField(max_length=6)
    sei_numero = models.CharField(max_length=30)
    doc = models.CharField(max_length=100, blank=True, default="")
    data_inicio = models.DateField()
    data_fim = models.DateField(null=True, blank=True)
    carater_excepcional = models.BooleanField(default=False)
    impedimento_substituicao = models.CharField(
        max_length=50, 
        choices=ImpedimentoSubstituicao.choices, 
        blank=True, 
        default=""
    )
    com_afastamento = models.BooleanField(default=False)
    possui_pendencia = models.BooleanField(default=False)
    pendencias = models.TextField(blank=True, default="")
    motivo_afastamento = models.TextField(blank=True, default="")

    # --- Vaga ---
    tipo_vaga = models.CharField(max_length=15, choices=TipoVaga.choices)
    cargo_vaga = models.IntegerField(choices=CargoVaga.choices, null=True, blank=True)

    # --- Controle ---
    criado_em = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'designacao'

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)