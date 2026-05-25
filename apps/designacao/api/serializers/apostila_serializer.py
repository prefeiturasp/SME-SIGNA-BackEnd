from rest_framework import serializers
from apps.designacao.models.apostila import Apostila
from apps.designacao.api.serializers.utils import validar_somente_numeros


class ApostilaSerializer(serializers.ModelSerializer):

    designacao = serializers.IntegerField(write_only=True)

    ato_apostilado = serializers.ChoiceField(
        choices=["designacao", "cessacao"],
        write_only=True
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
        if not data.get("designacao"):
            raise serializers.ValidationError(
                "Designação é obrigatória."
            )

        return data