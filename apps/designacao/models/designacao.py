"""Modelos de designação e impedimentos de substituição.

Define a designação e os impedimentos de substituição usados no fluxo
administrativo de nomeação e remoção de servidores.
"""

from django.db import models


class ServidorDesignacaoMixin(models.Model):
    """Campos de indicado e titular compartilhados entre Designacao
    e DesignacaoDetalhe.
    """

    # --- Indicado ---
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

    # --- Titular ---
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

    class Meta:
        abstract = True


class ImpedimentoSubstituicao(models.Model):
    """Representa um impedimento que pode afetar a substituição de
    atividade.
    """

    codigo = models.CharField(max_length=50, unique=True)
    descricao = models.CharField(max_length=255)

    class Meta:
        db_table = "impedimento_substituicao"

    def __str__(self) -> str:
        """Retorna a representação textual do impedimento de substituição.

        Returns:
            str: Descrição do impedimento.

        """
        return self.descricao
