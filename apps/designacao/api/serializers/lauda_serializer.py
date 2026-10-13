"""Serializador de entrada para geração da lauda de publicação.

Define o payload aceito por ``portarias/lauda/``: os atos selecionados na
tela de publicação do D.O. e o formato do arquivo desejado.
"""

from rest_framework import serializers

from apps.designacao.services.lauda_service import FormatoLauda


class LaudaRequestSerializer(serializers.Serializer):
    """Atos e formato para geração da lauda."""

    ids = serializers.ListField(
        child=serializers.IntegerField(min_value=1),
        allow_empty=False,
        help_text="IDs dos atos administrativos que compõem a lauda.",
    )
    formato = serializers.ChoiceField(
        choices=FormatoLauda.choices,
        default=FormatoLauda.PDF,
        help_text="Formato do arquivo gerado: PDF ou WORD (.docx).",
    )

    def validate_ids(self, value: list[int]) -> list[int]:
        """Remove ids repetidos preservando a ordem informada.

        Args:
            value: Lista de ids recebida no payload.

        Returns:
            list[int]: Ids únicos, na ordem original.

        """
        return list(dict.fromkeys(value))
