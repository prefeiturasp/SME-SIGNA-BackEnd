"""Serializador de entrada para geração da lauda de publicação.

Define o payload aceito por ``portarias/lauda/``: os atos selecionados na
tela de publicação do D.O., o formato do arquivo e a ordem dos atos.
"""

from rest_framework import serializers

from apps.designacao.services.lauda_service import (
    FormatoLauda,
    OrdenacaoLauda,
)


class LaudaRequestSerializer(serializers.Serializer):
    """Atos, formato e ordenação para geração da lauda."""

    ids = serializers.ListField(
        child=serializers.IntegerField(min_value=1),
        allow_empty=False,
        help_text="IDs dos atos administrativos que compõem a lauda.",
    )
    formato = serializers.ChoiceField(
        choices=FormatoLauda.choices,
        default=FormatoLauda.PDF,
        help_text="Formato do arquivo gerado: PDF, WORD (.docx) ou CSV.",
    )
    ordenacao = serializers.ChoiceField(
        choices=OrdenacaoLauda.choices,
        help_text="Ordem dos atos no arquivo: NUMERO_PORTARIA (nº de "
        "portaria), DRE (nome da DRE em ordem alfabética) ou TITULO "
        "(título do ato em ordem alfabética).",
    )

    def validate_ids(self, value: list[int]) -> list[int]:
        """Remove ids repetidos preservando a ordem informada.

        Args:
            value: Lista de ids recebida no payload.

        Returns:
            list[int]: Ids únicos, na ordem original.

        """
        return list(dict.fromkeys(value))
