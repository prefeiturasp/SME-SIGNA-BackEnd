"""Exception handler customizado da API.

Garante que toda resposta de erro da DRF inclua uma chave `detail` com uma
mensagem legível, mesmo quando o corpo original é um dicionário de erros por
campo (comportamento padrão de `ValidationError` em serializers). Sem isso,
clientes que só leem `detail` (como o front-end) recebem uma mensagem
genérica em vez do motivo real da falha de validação.
"""

from typing import Any

from rest_framework.response import Response
from rest_framework.views import exception_handler as drf_exception_handler


def _flatten_errors(errors: Any, prefix: str = "") -> list[str]:
    """Achata um corpo de erro da DRF (dict/list aninhado) em mensagens.

    Args:
        errors: Corpo de erro retornado pela DRF (dict, list ou str).
        prefix: Caminho do campo acumulado até este ponto, usado para
            identificar a origem de cada mensagem em estruturas aninhadas.

    Returns:
        list[str]: Mensagens no formato "campo: mensagem".

    """
    mensagens: list[str] = []

    if isinstance(errors, dict):
        for campo, valor in errors.items():
            novo_prefixo = f"{prefix}.{campo}" if prefix else str(campo)
            mensagens.extend(_flatten_errors(valor, novo_prefixo))
    elif isinstance(errors, list):
        for item in errors:
            mensagens.extend(_flatten_errors(item, prefix))
    else:
        mensagens.append(f"{prefix}: {errors}" if prefix else str(errors))

    return mensagens


def exception_handler(exc: Exception, context: dict) -> Response | None:
    """Adiciona um resumo legível (`detail`) às respostas de erro da DRF.

    Preserva o corpo padrão da DRF (por exemplo, erros por campo) e, quando
    ele ainda não possui `detail`, adiciona um resumo com todas as
    mensagens de erro concatenadas.

    Args:
        exc: Exceção capturada pela DRF.
        context: Contexto da exceção fornecido pela DRF.

    Returns:
        Response | None: Resposta de erro da DRF com `detail` preenchido,
        ou None se a exceção não for tratável pela DRF.

    """
    response = drf_exception_handler(exc, context)

    if response is None:
        return response

    if isinstance(response.data, dict) and "detail" in response.data:
        return response

    detail = "; ".join(_flatten_errors(response.data)) or "Erro de validação."

    if isinstance(response.data, dict):
        response.data["detail"] = detail
    else:
        response.data = {"detail": detail, "errors": response.data}

    return response
