"""Modelo de regra de portaria.

Define o cadastro de regras que configuram como um cargo é tratado na
composição das Portarias, incluindo os dados usados na publicação oficial.
"""

from django.db import models


class RegraPortaria(models.Model):
    """Representa uma regra de portaria cadastrada para um cargo."""

    class Status(models.TextChoices):
        ATIVO = "ATIVO", "Ativo"
        INATIVO = "INATIVO", "Inativo"

    class TipoModulo(models.TextChoices):
        ESPECIFICO_SUPERVISOR = (
            "ESPECIFICO_SUPERVISOR",
            "Específico - supervisor",
        )
        NENHUM = "NENHUM", "Nenhum"
        TURMAS = "TURMAS", "Turmas"

    class Emitente(models.TextChoices):
        SECRETARIO_MUNICIPAL_EDUCACAO = (
            "SECRETARIO_MUNICIPAL_EDUCACAO",
            "Secretário municipal de educação",
        )

    # --- Identificação ---
    descricao_resumida_cargo = models.CharField(
        "Descrição resumida do cargo", max_length=255
    )
    descricao_completa_cargo = models.CharField(
        "Descrição completa do cargo", max_length=255
    )
    codigo_cargo_eol = models.CharField(
        "Código do cargo no EOL", max_length=20, unique=True
    )
    tipo_modulo = models.CharField(
        "Tipo de módulo",
        max_length=25,
        choices=TipoModulo.choices,
    )
    status = models.CharField(
        max_length=10,
        choices=Status.choices,
        default=Status.ATIVO,
    )

    # --- Publicação ---
    texto_publicacao = models.TextField("Texto para publicação (provimento)")
    emitente = models.CharField(
        max_length=40,
        choices=Emitente.choices,
    )
    normas = models.TextField(blank=True, default="")
    observacoes = models.TextField(blank=True, default="")
    utilizar_numero_sei = models.BooleanField("Utilizar Nº SEI", default=False)

    criado_em = models.DateTimeField(auto_now_add=True)
    atualizado_em = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "regra_portaria"
        ordering = ["descricao_resumida_cargo"]

    def __str__(self) -> str:
        """Retorna a representação textual da regra de portaria.

        Returns:
            str: Descrição resumida do cargo.

        """
        return self.descricao_resumida_cargo
