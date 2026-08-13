"""Modelo de cargo base.

Define o cadastro de cargos base utilizados na parametrização do sistema,
com dados vindos do EOL complementados por informações de gestão.
"""

from django.db import models


class CargoBase(models.Model):
    """Representa um cargo base cadastrado a partir de um cargo do EOL."""

    class Grupamento(models.TextChoices):
        APOIO_EDUCACAO = "APOIO_EDUCACAO", "Apoio - educação"
        DOCENTES = "DOCENTES", "Docentes"
        GESTORES_EDUCACAO = "GESTORES_EDUCACAO", "Gestores - educação"

    class SituacaoFuncional(models.TextChoices):
        COMISSIONADO = "COMISSIONADO", "Cargo em comissão"
        EFETIVO = "EFETIVO", "Efetivo"
        CONTRATADO = "CONTRATADO", "Contratado"

    class Status(models.TextChoices):
        ATIVO = "ATIVO", "Ativo"
        INATIVO = "INATIVO", "Inativo"
        EXTINTO = "EXTINTO", "Extinto"

    # --- Dados do cargo no EOL ---
    codigo_cargo = models.CharField(
        "Código cargo no EOL", max_length=20, unique=True
    )
    descricao_completa = models.CharField("Descrição completa", max_length=255)

    # --- Dados complementares de gestão ---
    descricao_resumida = models.CharField("Descrição resumida", max_length=255)
    grupamento = models.CharField(max_length=20, choices=Grupamento.choices)
    situacao_funcional = models.CharField(
        "Situação funcional",
        max_length=20,
        choices=SituacaoFuncional.choices,
    )
    status = models.CharField(
        max_length=10,
        choices=Status.choices,
        default=Status.ATIVO,
    )

    # --- Utilização do cargo ---
    utilizado_para_funcoes = models.BooleanField(
        "Utilizado para funções", default=True
    )
    utilizado_para_designacoes = models.BooleanField(
        "Utilizado para designações", default=True
    )
    utilizado_para_ste = models.BooleanField(
        "Utilizado para STE", default=True
    )
    utilizado_para_permutas = models.BooleanField(
        "Utilizado para permutas", default=False
    )
    cargo_base_ficticio = models.BooleanField(
        "Cargo base fictício", default=False
    )

    criado_em = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "cargo_base"
        ordering = ["descricao_resumida"]

    def __str__(self) -> str:
        """Retorna a representação textual do cargo base.

        Returns:
            str: Código do cargo e descrição resumida.

        """
        return f"{self.codigo_cargo} - {self.descricao_resumida}"
