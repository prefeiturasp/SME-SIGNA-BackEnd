"""Serializador para cessação de designações.

Inclui informações de insubsistência e validações específicas de portaria e
ano.
"""

from rest_framework import serializers

from apps.designacao.api.serializers.insubsistencia_serializer import (
    InsubsistenciaSerializer,
)
from apps.designacao.api.serializers.utils import validar_somente_numeros
from apps.designacao.models.cessacao import Cessacao


class CessacaoSerializer(serializers.ModelSerializer):
    """Serializador de Cessação.

    Recupera dados relacionados à insubsistência e valida campos numéricos.
    """

    insubsistencia = serializers.SerializerMethodField()

    class Meta:
        model = Cessacao
        fields = "__all__"

    def get_insubsistencia(self, obj):
        """Retorna a insubsistência mais recente associada à cessação.

        Args:
            obj: Instância de Cessacao.

        Returns:
            dict|None: Dados serializados da insubsistência, ou None se não
            existir.
        """
        insubsistencia = (
            obj.insubsistencia.filter(is_deleted=False)
            .order_by("-criado_em")
            .first()
        )
        if insubsistencia and not insubsistencia.is_deleted:
            return InsubsistenciaSerializer(insubsistencia).data

        return None

    def validate_numero_portaria(self, value):
        """Valida o número da portaria apenas com dígitos.

        Args:
            value: Número da portaria recebido.

        Returns:
            str: Valor validado contendo apenas números.
        """
        return validar_somente_numeros(value)

    def validate_ano_vigente(self, value):
        """Valida o ano vigente apenas com dígitos.

        Args:
            value: Ano vigente recebido.

        Returns:
            str: Valor validado contendo apenas números.
        """
        return validar_somente_numeros(value)

    def validate(self, data):
        """Valida a consistência dos dados de cessação.

        Args:
            data: Dicionário com os dados de cessação.

        Raises:
            serializers.ValidationError: Se a designação já possuir cessação
            associada.

        Returns:
            dict: Dados validados.
        """
        designacao = data.get("designacao")

        if designacao and hasattr(designacao, "cessacao"):
            raise serializers.ValidationError(
                "Esta designação já possui uma cessação cadastrada."
            )

        return data
