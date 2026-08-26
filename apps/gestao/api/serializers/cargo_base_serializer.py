"""Serializadores de cargo base.

Define os payloads de leitura e escrita para o cadastro e a consulta de
cargos base.
"""

import logging

import environ
from rest_framework import serializers

from apps.gestao.models.cargo_base import CargoBase

env = environ.Env()


MSG_LICENCA_OBRIGATORIO = (
    "É necessário informar uma quantidade máxima de dias de licença válida."
)
MSG_LICENCA_INVALIDO = (
    "Quantidade máxima de dias de licença não informada ou inválida"
)
MSG_LICENCA_ZERADA = (
    "Quantidade máxima de dias de licença deve ser maior que zero"
)
logger = logging.getLogger(__name__)


def validate_quantidade_maxima_de_dias_de_licenca(attrs: dict) -> dict:
    """Valida quantidade máxima de dias de licença.

    Args:
        attrs: Dicionário com os dados validados do cargo base.

    Returns:
        True: Se os dados são válidos.
        Exception: Se os dados não são válidos.

    """
    pesquisar_licencas_no_sigpec = attrs.get("pesquisar_licencas_no_sigpec")
    quantidade_maxima_de_dias_de_licenca = attrs.get(
        "quantidade_maxima_de_dias_de_licenca"
    )

    if (
        pesquisar_licencas_no_sigpec
        and quantidade_maxima_de_dias_de_licenca == 0
    ):
        logger.warning(MSG_LICENCA_INVALIDO)
        raise serializers.ValidationError(
            {"quantidade_maxima_de_dias_de_licenca": MSG_LICENCA_ZERADA}
        )

    if (
        pesquisar_licencas_no_sigpec
        and not quantidade_maxima_de_dias_de_licenca
    ):
        logger.warning(MSG_LICENCA_INVALIDO)
        raise serializers.ValidationError(
            {"quantidade_maxima_de_dias_de_licenca": MSG_LICENCA_OBRIGATORIO}
        )

    return attrs


class CargoBaseReadSerializer(serializers.ModelSerializer):
    """Serializador de leitura para cargo base."""

    grupamento_display = serializers.CharField(
        source="get_grupamento_display", read_only=True
    )
    situacao_funcional_display = serializers.CharField(
        source="get_situacao_funcional_display", read_only=True
    )
    status_display = serializers.CharField(
        source="get_status_display", read_only=True
    )

    class Meta:
        model = CargoBase
        fields = [
            "id",
            "codigo_cargo",
            "descricao_completa",
            "descricao_resumida",
            "grupamento",
            "grupamento_display",
            "situacao_funcional",
            "situacao_funcional_display",
            "status",
            "status_display",
            "utilizado_para_funcoes",
            "utilizado_para_designacoes",
            "utilizado_para_ste",
            "utilizado_para_permutas",
            "cargo_base_ficticio",
            "testar_laudo",
            "pesquisar_licencas_no_sigpec",
            "quantidade_maxima_de_dias_de_licenca",
            "criado_em",
        ]


class CargoBaseWriteSerializer(serializers.ModelSerializer):
    """Serializador de escrita para cadastro de cargo base."""

    class Meta:
        model = CargoBase
        fields = [
            "codigo_cargo",
            "descricao_completa",
            "descricao_resumida",
            "grupamento",
            "situacao_funcional",
            "status",
            "utilizado_para_funcoes",
            "utilizado_para_designacoes",
            "utilizado_para_ste",
            "utilizado_para_permutas",
            "cargo_base_ficticio",
            "testar_laudo",
            "pesquisar_licencas_no_sigpec",
            "quantidade_maxima_de_dias_de_licenca",
        ]
        extra_kwargs = {
            "status": {"required": False},
            "utilizado_para_funcoes": {"required": False},
            "utilizado_para_designacoes": {"required": False},
            "utilizado_para_ste": {"required": False},
            "utilizado_para_permutas": {"required": False},
            "cargo_base_ficticio": {"required": False},
            "testar_laudo": {"required": False},
            "pesquisar_licencas_no_sigpec": {"required": False},
            "quantidade_maxima_de_dias_de_licenca": {"required": False},
        }

    def validate(self, attrs: dict) -> dict:
        """Valida os dados de um cargo base.

        Args:
            attrs: Dicionário com os dados validados do cargo base.

        Returns:
            True: Se os dados são válidos.
            Exception: Se os dados não são válidos.

        """
        response = validate_quantidade_maxima_de_dias_de_licenca(attrs)
        return response


class CargoBaseUpdateSerializer(serializers.ModelSerializer):
    """Serializador de atualização para cargo base.

    Não expõe `codigo_cargo` e `descricao_completa`, pois são dados de
    origem vindos do EOL e não podem ser alterados após o cadastro.
    """

    class Meta:
        model = CargoBase
        fields = [
            "descricao_resumida",
            "grupamento",
            "situacao_funcional",
            "status",
            "utilizado_para_funcoes",
            "utilizado_para_designacoes",
            "utilizado_para_ste",
            "utilizado_para_permutas",
            "cargo_base_ficticio",
            "testar_laudo",
            "pesquisar_licencas_no_sigpec",
            "quantidade_maxima_de_dias_de_licenca",
        ]

    def validate(self, attrs: dict) -> dict:
        """Valida os dados de um cargo base.

        Args:
            attrs: Dicionário com os dados validados do cargo base.

        Returns:
            True: Se os dados são válidos.
            Exception: Se os dados não são válidos.

        """
        response = validate_quantidade_maxima_de_dias_de_licenca(attrs)
        return response
