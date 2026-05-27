"""Serializador para criação e validação de apostilas.

O serializador expõe os campos necessários para vincular uma apostila a uma
designação
ou cessação, além de validar a presença obrigatória da designação.
"""

from rest_framework import serializers

from apps.designacao.models.apostila import Apostila


class ApostilaSerializer(serializers.ModelSerializer):
    """Serializador de Apostila.

    Valida os dados de apostila e garante que a designação associada esteja
    presente.
    """

    designacao = serializers.IntegerField(write_only=True)

    ato_apostilado = serializers.ChoiceField(
        choices=["designacao", "cessacao"], write_only=True
    )

    class Meta:
        model = Apostila
        fields = [
            "id",
            "tipo",
            "designacao",
            "ato_apostilado",
            "sei_numero",
            "observacao",
            "d_o",
        ]

    def validate(self, data):
        """Valida o payload completo de apostila.

        Args:
            data: Dicionário com os dados da apostila.

        Raises:
            serializers.ValidationError: Se o campo de designação estiver
            ausente.

        Returns:
            dict: Dados validados.
        """
        if not data.get("designacao"):
            raise serializers.ValidationError("Designação é obrigatória.")

        return data
