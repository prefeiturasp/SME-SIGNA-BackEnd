"""Modelo de modelo de texto de portaria.

Define o cadastro de modelos de texto usados na emissão de portarias,
com variáveis (placeholders) que são substituídas pelos dados reais no
momento da emissão. Apostilas e insubsistências têm um modelo por
combinação de `tipo_portaria` e `tipo_ato_pai`, já que seu texto varia
conforme o tipo do ato de origem (ex.: apostila de designação x apostila
de cessação).
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
        CARGO = "CARGO", "Cargo a ser ocupado"
        CARGO_INDICADO = "CARGO_INDICADO", "Cargo do servidor indicado"
        CATEGORIA = "CATEGORIA", "Categoria"
        UNIDADE = "UNIDADE", "Unidade"
        CARGO_DESIGNACAO = "CARGO_DESIGNACAO", "Cargo da designação"
        UNIDADE_PROPONENTE = "UNIDADE_PROPONENTE", "Unidade proponente"
        TIPO_DE_CARGO = "TIPO_DE_CARGO", "Tipo de cargo"
        DATA_INICIAL = "DATA_INICIAL", "Data inicial"

        # Designação não tem ato pai, então nunca leva tipo_ato_pai. Os
        # demais tipos sempre levam — mesmo cessação, que só tem um pai
        # possível (designação): a tela de cadastro usa isso para exibir
        # "Cessação de Designação" de forma consistente com "Apostila de
        # Designação/Cessação" e "Insubsistência de X" na listagem.
        #
        # Mesma regra de hierarquia usada por `AtoAdministrativo.clean()` —
        # reaproveitada daqui para não duplicar a definição.

        UNIDADE_ADMINISTRATIVA = (
            "UNIDADE_ADMINISTRATIVA",
            "Unidade administrativa",
        )
        ANO_PORTARIA = "ANO_PORTARIA", "Ano da portaria"
        CARGO_BASE = "CARGO_BASE", "Cargo base"
        EH = "EH", "Estrutura hierárquica"
        TITULAR = "TITULAR", "Titular"

    VARIAVEIS_POR_TIPO_CARGO: dict[str, str] = {
        Variavel.TITULAR: TipoCargo.CARGO_DISPONIVEL,
    }

    TIPOS_QUE_VARIAM_POR_ATO_PAI = AtoAdministrativo.TIPOS_PAI_VALIDOS

    tipo_portaria = models.CharField(
        "Tipo de portaria",
        max_length=20,
        choices=AtoAdministrativo.Tipo.choices,
    )
    tipo_ato_pai = models.CharField(
        "Tipo do ato pai",
        max_length=20,
        choices=AtoAdministrativo.Tipo.choices,
        blank=True,
        default="",
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
        ordering = ["-criado_em"]

    def __str__(self) -> str:
        """Retorna a representação textual do modelo de portaria.

        Returns:
            str: Nome do modelo.

        """
        return self.nome_modelo

    @classmethod
    def variaveis_disponiveis(
        cls, tipo_cargo: str | None = None
    ) -> list[tuple[str, str]]:
        """Retorna as variáveis oferecidas para um tipo de cargo.

        Sem `tipo_cargo`, devolve todas as variáveis, preservando o
        contrato anterior do endpoint. Com `tipo_cargo`, omite as
        variáveis de `VARIAVEIS_POR_TIPO_CARGO` que não pertencem ao
        tipo informado.

        Args:
            tipo_cargo: Tipo de cargo do modelo (`CARGO_VAGO`,
                `CARGO_DISPONIVEL`) ou None para não restringir.

        Returns:
            list[tuple[str, str]]: Pares (valor, rótulo) disponíveis.

        """
        if tipo_cargo is None:
            return list(cls.Variavel.choices)
        return [
            (valor, rotulo)
            for valor, rotulo in cls.Variavel.choices
            if cls.VARIAVEIS_POR_TIPO_CARGO.get(valor, tipo_cargo)
            == tipo_cargo
        ]

    @classmethod
    def variaveis_invalidas_para_tipo_cargo(
        cls, variaveis: list[str], tipo_cargo: str
    ) -> list[str]:
        """Retorna as variáveis que não valem para o tipo de cargo.

        Args:
            variaveis: Chaves de variáveis escolhidas para o modelo.
            tipo_cargo: Tipo de cargo do modelo.

        Returns:
            list[str]: Variáveis restritas a outro tipo de cargo.

        """
        return [
            valor
            for valor in variaveis
            if cls.VARIAVEIS_POR_TIPO_CARGO.get(valor, tipo_cargo)
            != tipo_cargo
        ]
