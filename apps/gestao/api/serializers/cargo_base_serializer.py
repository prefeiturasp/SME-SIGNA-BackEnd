"""Serializadores de cargo base.

Define os payloads de leitura e escrita para o cadastro e a consulta de
cargos base.
"""

from rest_framework import serializers

from apps.gestao.models.cargo_base import CargoBase


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
        ]
        extra_kwargs = {
            "status": {"required": False},
        }


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
        ]
