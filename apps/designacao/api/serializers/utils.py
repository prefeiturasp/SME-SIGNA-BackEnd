from rest_framework import serializers


class NullableDateField(serializers.DateField):
    """DateField que converte string vazia para None."""

    def to_internal_value(self, value):
        if value == "":
            return None
        return super().to_internal_value(value)


def validar_somente_numeros(value):
    if not value.isdigit():
        raise serializers.ValidationError("Deve conter apenas números.")
    return value


def extrair_mensagem_erro(detail):
    """
    Transforma qualquer estrutura de erro do DRF em uma string única.
    """
    if isinstance(detail, dict):
        item = next(iter(detail.values()))
        return extrair_mensagem_erro(item)

    if isinstance(detail, list) and detail:
        return extrair_mensagem_erro(detail[0])

    return str(detail)
