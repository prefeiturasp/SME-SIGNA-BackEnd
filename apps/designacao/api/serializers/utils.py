"""Utilitários de serialização para o aplicativo de designação.

Contém funções auxiliares para validação e formatação de mensagens de erro
usadas pelos serializadores da API.
"""

from typing import Any

from rest_framework import serializers


class NullableDateField(serializers.DateField):
    """Campo de data que aceita string vazia como valor nulo.

    Este campo especial permite que strings vazias sejam convertidas em None,
    em vez de disparar um erro de validação do DRF.
    """

    def to_internal_value(self, value: Any) -> Any:
        """Converte o valor de entrada para o valor interno do campo.

        Args:
            value: Valor de entrada que pode ser uma string vazia ou data.

        Returns:
            datetime.date | None: Data validada ou None quando a string estiver
            vazia.
        """
        if value == "":
            return None
        return super().to_internal_value(value)


def validar_somente_numeros(value: str) -> str:
    """Valida se uma string contém apenas dígitos.

    Args:
        value: Texto a ser validado.

    Raises:
        serializers.ValidationError: Se o valor contiver caracteres não
        numéricos.

    Returns:
        str: Valor original se for composto apenas por dígitos.
    """
    if not value.isdigit():
        raise serializers.ValidationError("Deve conter apenas números.")
    return value


def extrair_mensagem_erro(detail: dict | list | str) -> str:
    """Extrai mensagem de erro de uma estrutura de detalhe do DRF.

    Args:
        detail: Estrutura de erro retornada pelo DRF, que pode ser dict, list
        ou outro.

    Returns:
        str: Mensagem de erro unificada.
    """
    if isinstance(detail, dict):
        item = next(iter(detail.values()))
        return extrair_mensagem_erro(item)

    if isinstance(detail, list) and detail:
        return extrair_mensagem_erro(detail[0])

    return str(detail)
