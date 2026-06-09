"""Modelo de detalhes de designação.

Define os campos de unidade, indicado, titular, período e sinalizadores
para o detalhe de uma designação.
"""

from django.db import models

from apps.designacao.models.ato_administrativo import AtoAdministrativo
from apps.designacao.models.designacao import (
    ImpedimentoSubstituicao,
    ServidorDesignacaoMixin,
)


class DesignacaoDetalhe(ServidorDesignacaoMixin):
    """Representa os detalhes complementares de uma designação."""

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
    def get_cargos_formatados(cls) -> list:
        """Retorna os cargos de vaga formatados para consumo da API.

        Converte os valores definidos em `CargoVaga` para uma lista
        de dicionários contendo código e nome do cargo.

        Returns:
            list[dict]: Lista de cargos formatados com código e descrição.

        """
        return [
            {"codigoCargo": c.value, "nomeCargo": c.label}
            for c in cls.CargoVaga
        ]
