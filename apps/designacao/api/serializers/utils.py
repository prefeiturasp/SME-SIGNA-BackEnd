

from rest_framework import serializers

def validar_somente_numeros(value):
    if not value.isdigit():
        raise serializers.ValidationError("Deve conter apenas números.")
    return value
