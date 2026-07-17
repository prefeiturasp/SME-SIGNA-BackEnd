"""Serializadores para insubsistência.

Inclui definição de payloads para escrita e leitura de insubsistência em atos.
"""

from rest_framework import serializers

from apps.designacao.api.serializers.ato_relacionado_mixin import (
    AtoRelacionadoMixin,
)
from apps.designacao.api.serializers.utils import (
    NullableDateField,
    validar_somente_numeros,
)
from apps.designacao.models.ato_administrativo import AtoAdministrativo


class InsubsistenciaWriteSerializer(serializers.Serializer):
    """Serializador de escrita para insubsistência.

    Valida os campos obrigatórios para criação de uma insubsistência.
    """

    ato_pai = serializers.PrimaryKeyRelatedField(
        queryset=AtoAdministrativo.objects.all()
    )
    numero_portaria = serializers.CharField(max_length=20)
    ano_vigente = serializers.CharField(max_length=6)
    sei_numero = serializers.CharField(max_length=30)
    doc = NullableDateField(required=False, default=None, allow_null=True)
    observacoes = serializers.CharField(
        allow_blank=True, required=False, default=""
    )
    texto_apostila = serializers.CharField(
        allow_blank=True, required=False, default=""
    )

    def validate_numero_portaria(self, value: str) -> str:
        """Valida que o número da portaria contenha apenas dígitos.

        Args:
            value: Valor do número da portaria.

        Returns:
            str: Valor validado com apenas dígitos.

        """
        return validar_somente_numeros(value)

    def validate_ano_vigente(self, value: str) -> str:
        """Valida que o ano vigente contenha apenas dígitos.

        Args:
            value: Valor do ano vigente.

        Returns:
            str: Valor validado com apenas dígitos.

        """
        return validar_somente_numeros(value)


class InsubsistenciaReadSerializer(
    AtoRelacionadoMixin, serializers.ModelSerializer
):
    """Serializador de leitura para insubsistência.

    Expõe status e observações da insubsistência.
    """

    status = serializers.SerializerMethodField()
    observacoes = serializers.CharField(
        source="insubsistencia_detalhe.observacoes", read_only=True
    )
    texto_apostila = serializers.SerializerMethodField()
    designacao = serializers.SerializerMethodField()
    cessacao = serializers.SerializerMethodField()

    class Meta:
        model = AtoAdministrativo
        fields = [
            "id",
            "tipo",
            "status",
            "ato_pai_id",
            "numero_portaria",
            "ano_vigente",
            "sei_numero",
            "doc",
            "criado_em",
            "observacoes",
            "texto_apostila",
            "designacao",
            "cessacao",
        ]

    def get_status(self, obj: AtoAdministrativo) -> str:
        """Retorna o status do ato de insubsistência.

        Args:
            obj: Instância de AtoAdministrativo.

        Returns:
            str: Status do ato.

        """
        return obj.status

    def get_texto_apostila(self, obj: AtoAdministrativo) -> str | None:
        """Retorna o texto da anulação quando a insubsistência é de apostila.

        Args:
            obj: Instância de AtoAdministrativo.

        Returns:
            str | None: Texto da anulação ou None se não aplicável.

        """
        detalhe = getattr(obj, "insubsistencia_apostila_detalhe", None)
        return detalhe.texto if detalhe else None
