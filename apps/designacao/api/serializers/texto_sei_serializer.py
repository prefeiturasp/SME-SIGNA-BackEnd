"""Serializadores para pré-visualização do texto SEI.

Define o payload de entrada para gerar o texto de um ato a partir do
modelo de portaria vigente, e o payload de saída com o texto gerado.
"""

from rest_framework import serializers

from apps.designacao.models.ato_administrativo import AtoAdministrativo


class TextoSeiPreviewRequestSerializer(serializers.Serializer):
    """Dados necessários para gerar a prévia do texto SEI de um ato."""

    tipo_portaria = serializers.ChoiceField(
        choices=AtoAdministrativo.Tipo.choices
    )
    tipo_ato_pai = serializers.ChoiceField(
        choices=AtoAdministrativo.Tipo.choices,
        required=False,
        allow_blank=True,
        default="",
    )
    dados = serializers.DictField(
        child=serializers.CharField(allow_blank=True, allow_null=True),
        required=False,
        default=dict,
    )


class TextoSeiPreviewResponseSerializer(serializers.Serializer):
    """Resposta com o modelo usado e o texto SEI gerado."""

    modelo_portaria_id = serializers.IntegerField()
    texto = serializers.CharField()
