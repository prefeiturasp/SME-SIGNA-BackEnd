"""Serializadores de regra de portaria.

Define os payloads de leitura e escrita para o cadastro, a consulta e a
edição de regras de portaria.
"""

from rest_framework import serializers

from apps.gestao.models.regra_portaria import RegraPortaria


class RegraPortariaReadSerializer(serializers.ModelSerializer):
    """Serializador de leitura para regra de portaria."""

    tipo_modulo_display = serializers.CharField(
        source="get_tipo_modulo_display", read_only=True
    )
    status_display = serializers.CharField(
        source="get_status_display", read_only=True
    )
    emitente_display = serializers.CharField(
        source="get_emitente_display", read_only=True
    )

    class Meta:
        model = RegraPortaria
        fields = [
            "id",
            "descricao_resumida_cargo",
            "descricao_completa_cargo",
            "codigo_cargo_eol",
            "tipo_modulo",
            "tipo_modulo_display",
            "status",
            "status_display",
            "texto_publicacao",
            "emitente",
            "emitente_display",
            "normas",
            "observacoes",
            "utilizar_numero_sei",
            "criado_em",
            "atualizado_em",
        ]


class RegraPortariaWriteSerializer(serializers.ModelSerializer):
    """Serializador de escrita para cadastro de regra de portaria."""

    class Meta:
        model = RegraPortaria
        fields = [
            "descricao_resumida_cargo",
            "descricao_completa_cargo",
            "codigo_cargo_eol",
            "tipo_modulo",
            "status",
            "texto_publicacao",
            "emitente",
            "normas",
            "observacoes",
            "utilizar_numero_sei",
        ]
        extra_kwargs = {
            "status": {"required": False},
            "normas": {"required": False},
            "observacoes": {"required": False},
            "utilizar_numero_sei": {"required": False},
        }


class RegraPortariaUpdateSerializer(serializers.ModelSerializer):
    """Serializador de atualização para regra de portaria."""

    class Meta:
        model = RegraPortaria
        fields = [
            "descricao_resumida_cargo",
            "descricao_completa_cargo",
            "codigo_cargo_eol",
            "tipo_modulo",
            "status",
            "texto_publicacao",
            "emitente",
            "normas",
            "observacoes",
            "utilizar_numero_sei",
        ]
