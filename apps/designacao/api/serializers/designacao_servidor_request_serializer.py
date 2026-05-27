"""Serializador para requisição de servidores por RF.

Utilizado para validar payloads que contêm apenas a RF do servidor solicitante.
"""

from rest_framework import serializers


class DesignacaoServidorRequestSerializer(serializers.Serializer):
    """Serializador simples contendo a RF do servidor."""

    rf = serializers.CharField()
