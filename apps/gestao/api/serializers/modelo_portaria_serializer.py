"""Serializadores de modelo de portaria.

Define os payloads de leitura e escrita para o cadastro e a consulta de
modelos de texto de portaria.
"""

from rest_framework import serializers

from apps.designacao.models.ato_administrativo import AtoAdministrativo
from apps.gestao.models.modelo_portaria import ModeloPortaria


class ModeloPortariaReadSerializer(serializers.ModelSerializer):
    """Serializador de leitura para modelo de portaria."""

    tipo_portaria_display = serializers.CharField(
        source="get_tipo_portaria_display", read_only=True
    )
    tipo_ato_pai_display = serializers.CharField(
        source="get_tipo_ato_pai_display", read_only=True
    )
    status_display = serializers.CharField(
        source="get_status_display", read_only=True
    )
    tipo_cargo_display = serializers.CharField(
        source="get_tipo_cargo_display", read_only=True
    )

    class Meta:
        model = ModeloPortaria
        fields = [
            "id",
            "tipo_portaria",
            "tipo_portaria_display",
            "tipo_ato_pai",
            "tipo_ato_pai_display",
            "status",
            "status_display",
            "nome_modelo",
            "tipo_cargo",
            "tipo_cargo_display",
            "variaveis",
            "observacoes",
            "texto_portaria",
            "criado_em",
            "atualizado_em",
        ]


class ModeloPortariaWriteSerializer(serializers.ModelSerializer):
    """Serializador de escrita para cadastro de modelo de portaria."""

    variaveis = serializers.ListField(
        child=serializers.ChoiceField(choices=ModeloPortaria.Variavel.choices),
        required=False,
    )
    tipo_ato_pai = serializers.ChoiceField(
        choices=AtoAdministrativo.Tipo.choices,
        required=False,
        allow_null=True,
    )

    class Meta:
        model = ModeloPortaria
        fields = [
            "tipo_portaria",
            "tipo_ato_pai",
            "status",
            "nome_modelo",
            "tipo_cargo",
            "variaveis",
            "observacoes",
            "texto_portaria",
        ]
        extra_kwargs = {
            "status": {"required": False},
        }

    def validate(self, attrs: dict) -> dict:
        """Garante consistência entre `tipo_portaria` e `tipo_ato_pai`.

        Designação e cessação não têm tipo de ato pai variável (só há uma
        combinação possível), então `tipo_ato_pai` deve ficar vazio.
        Apostila e insubsistência exigem `tipo_ato_pai` dentre os tipos de
        ato pai válidos para aquele tipo, conforme
        `AtoAdministrativo.TIPOS_PAI_VALIDOS`.

        Args:
            attrs: Dados já validados individualmente pelos campos.

        Returns:
            dict: Dados validados.

        Raises:
            serializers.ValidationError: Quando `tipo_ato_pai` é
            inconsistente com `tipo_portaria`.

        """
        tipo_portaria: str = attrs.get(
            "tipo_portaria", getattr(self.instance, "tipo_portaria", "")
        )
        tipo_ato_pai = attrs.get(
            "tipo_ato_pai", getattr(self.instance, "tipo_ato_pai", None)
        )
        tipos_validos = AtoAdministrativo.TIPOS_PAI_VALIDOS.get(
            tipo_portaria, set()
        )

        if tipos_validos:
            if tipo_ato_pai not in tipos_validos:
                raise serializers.ValidationError(
                    {
                        "tipo_ato_pai": (
                            f"Para tipo_portaria={tipo_portaria}, "
                            f"tipo_ato_pai deve ser um de {sorted(tipos_validos)}."  # noqa: E501
                        )
                    }
                )
        elif tipo_ato_pai:
            raise serializers.ValidationError(
                {
                    "tipo_ato_pai": (
                        f"tipo_portaria={tipo_portaria} não aceita "
                        "tipo_ato_pai."
                    )
                }
            )

        return attrs
