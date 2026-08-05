"""Serializadores de cargo base.

Define os payloads de leitura e escrita para o cadastro e a consulta de
cargos base.
"""

from rest_framework import serializers

from apps.gestao.models.cargo_base import CargoBase


class CargoBaseReadSerializer(serializers.ModelSerializer):
    """Serializador de leitura para cargo base."""

    class Meta:
        model = CargoBase
        fields = [
            "id",
            "codigo_cargo",
            "descricao_completa",
            "descricao_resumida",
            "grupamento",
            "situacao_funcional",
            "status",
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
