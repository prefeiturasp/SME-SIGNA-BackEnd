from rest_framework import serializers
from apps.designacao.models.cessacao import Cessacao


class CessacaoSerializer(serializers.ModelSerializer):

    class Meta:
        model = Cessacao
        fields = '__all__'

    def _validar_somente_numeros(self, value):
        if not value.isdigit():
            raise serializers.ValidationError("Deve conter apenas números.")
        return value

    def validate_numero_portaria(self, value):
        return self._validar_somente_numeros(value)

    def validate_ano_vigente(self, value):
        return self._validar_somente_numeros(value)

    def validate_sei_numero(self, value):
        return self._validar_somente_numeros(value)

    def validate(self, data):
        designacao = data.get('designacao')

        if designacao and hasattr(designacao, 'cessacao'):
            raise serializers.ValidationError(
                "Esta designação já possui uma cessação cadastrada."
            )

        return data