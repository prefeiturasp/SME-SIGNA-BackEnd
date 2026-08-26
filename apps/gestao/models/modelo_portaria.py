"""Modelo de modelo de texto de portaria.

Define o cadastro de modelos de texto usados na emissão de portarias,
com variáveis (placeholders) que são substituídas pelos dados reais no
momento da emissão.
"""

from django.db import models

from apps.designacao.models.ato_administrativo import AtoAdministrativo


class ModeloPortaria(models.Model):
    """Representa um modelo de texto cadastrado para emissão de portarias."""

    class Status(models.TextChoices):
        ATIVO = "ATIVO", "Ativo"
        INATIVO = "INATIVO", "Inativo"

    class TipoCargo(models.TextChoices):
        CARGO_VAGO = "CARGO_VAGO", "Cargo vago"
        CARGO_DISPONIVEL = "CARGO_DISPONIVEL", "Cargo disponível"

    class Variavel(models.TextChoices):
        PORTARIA = "PORTARIA", "Portaria"
        NUMERO_SEI = "NUMERO_SEI", "Nº SEI"
        NOME_SERVIDOR = "NOME_SERVIDOR", "Nome do servidor"
        NUMERO_RF = "NUMERO_RF", "Nº do RF"
        VINCULO = "VINCULO", "Vínculo"
        CARGO = "CARGO", "Cargo"
        CATEGORIA = "CATEGORIA", "Categoria"
        UNIDADE = "UNIDADE", "Unidade"
        CARGO_DESIGNACAO = "CARGO_DESIGNACAO", "Cargo da designação"
        UNIDADE_PROPONENTE = "UNIDADE_PROPONENTE", "Unidade proponente"
        TIPO_DE_CARGO = "TIPO_DE_CARGO", "Tipo de cargo"
        DATA_INICIAL = "DATA_INICIAL", "Data inicial"
        DIPLOMA = "DIPLOMA", "Diploma"
        PERIODO = "PERIODO", "Período"

    tipo_portaria = models.CharField(
        "Tipo de portaria",
        max_length=20,
        choices=AtoAdministrativo.Tipo.choices,
    )
    status = models.CharField(
        max_length=10,
        choices=Status.choices,
        default=Status.ATIVO,
    )
    nome_modelo = models.CharField("Nome do modelo", max_length=255)
    tipo_cargo = models.CharField(
        "Tipo de cargo",
        max_length=20,
        choices=TipoCargo.choices,
    )
    variaveis = models.JSONField("Variável", default=list, blank=True)
    observacoes = models.TextField(blank=True, default="")
    texto_portaria = models.TextField("Texto da portaria")

    criado_em = models.DateTimeField(auto_now_add=True)
    atualizado_em = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "modelo_portaria"
        ordering = ["nome_modelo"]

    def __str__(self) -> str:
        """Retorna a representação textual do modelo de portaria.

        Returns:
            str: Nome do modelo.

        """
        return self.nome_modelo
