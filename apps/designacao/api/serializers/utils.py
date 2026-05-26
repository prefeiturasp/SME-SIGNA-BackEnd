
"""Utilitários de serialização para o aplicativo de designação.

Contém funções auxiliares para validação e formatação de mensagens de erro
usadas pelos serializadores da API.
"""

from rest_framework import serializers


class NullableDateField(serializers.DateField):
    """DateField que converte string vazia para None."""

    def to_internal_value(self, value):
        if value == '':
            return None
        return super().to_internal_value(value)


def validar_somente_numeros(value):
    """Valida se uma string contém apenas dígitos.

    Args:
        value: Texto a ser validado.

    Raises:
        serializers.ValidationError: Se o valor contiver caracteres não numéricos.

    Returns:
        str: Valor original se for composto apenas por dígitos.
    """
    if not value.isdigit():
        raise serializers.ValidationError("Deve conter apenas números.")
    return value


def extrair_mensagem_erro(detail):
    """Extrai mensagem de erro de uma estrutura de detalhe do DRF.

    Args:
        detail: Estrutura de erro retornada pelo DRF, que pode ser dict, list ou outro.

    Returns:
        str: Mensagem de erro unificada.
    """
    if isinstance(detail, dict):
        item = next(iter(detail.values()))
        return extrair_mensagem_erro(item)
    
    if isinstance(detail, list) and detail:
        return extrair_mensagem_erro(detail[0])
    
    return str(detail)