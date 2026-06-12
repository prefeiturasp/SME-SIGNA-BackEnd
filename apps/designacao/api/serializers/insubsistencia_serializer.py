"""Serializador de insubsistências para API.

Contém validações de campos numéricos e regras de negócio para evitar
insubsistências duplicadas para o mesmo ato.
"""

from rest_framework import serializers

from apps.designacao.api.serializers.utils import validar_somente_numeros
from apps.designacao.models.insubsistencia import (
    Insubsistencia,
    TipoInsubsistencia,
)

# ── Legado ───────────────────────────────────────────────────────────────────


class InsubsistenciaSerializer(serializers.ModelSerializer):
    """Serializador de Insubsistência.

    Valida campos de portaria e ano, e garante unicidade conforme o tipo
    de insubsistência informada.
    """

    tipo_insubsistencia = serializers.ChoiceField(
        choices=TipoInsubsistencia.choices,
        write_only=True,
        required=True,
    )

    class Meta:
        model = Insubsistencia
        fields = "__all__"

    def validate_numero_portaria(self, value: str) -> str:
        """Valida o número da portaria como apenas dígitos.

        Args:
            value: Valor do número da portaria.

        Returns:
            str: Valor contendo apenas números.
        """
        return validar_somente_numeros(value)

    def validate_ano_vigente(self, value: str) -> str:
        """Valida o ano vigente como apenas dígitos.

        Args:
            value: Valor do ano vigente.

        Returns:
            str: Valor contendo apenas números.
        """
        return validar_somente_numeros(value)

    def create(self, validated_data: dict) -> Insubsistencia:
        """Cria a insubsistência removendo dados auxiliares de tipo.

        Args:
            validated_data: Dados já validados para criação.

        Returns:
            Insubsistencia: Instância criada do modelo.
        """
        validated_data.pop("tipo_insubsistencia", None)
        return super().create(validated_data)

    def validate(self, data: dict) -> dict:
        """Valida regras de negócio para insubsistência.

        Verifica se a designação está informada e garante que não haja
        insubsistências
        duplicadas para o mesmo tipo de ato.

        Args:
            data: Dicionário com os dados validados.

        Raises:
            serializers.ValidationError: Se a designação não estiver informada
            ou se já
                existir uma insubsistência para o mesmo ato.

        Returns:
            dict: Dados validados.
        """
        from apps.designacao.models.designacao import Designacao

        designacao = data.get("designacao")
        tipo_insubsistencia = data.get("tipo_insubsistencia")

        if not designacao:
            raise serializers.ValidationError(
                "Informe uma designação ou cessação para cadastrar a insubsistência."  # noqa: E501
            )

        if tipo_insubsistencia == TipoInsubsistencia.DESIGNACAO and designacao:
            queryset = Insubsistencia.objects.filter(
                designacao_id=designacao,
                is_deleted=False,
            )
            if queryset.exists():
                raise serializers.ValidationError(
                    "Esta designação já possui uma insubsistência cadastrada."
                )

        if tipo_insubsistencia == TipoInsubsistencia.CESSACAO and designacao:
            designacao_obj = (
                Designacao.objects.select_related("cessacao")
                .filter(
                    id=designacao.id,
                    is_deleted=False,
                )
                .first()
            )
            cessacao_relacionada = getattr(designacao_obj, "cessacao", None)
            queryset = (
                Insubsistencia.objects.filter(
                    cessacao_id=cessacao_relacionada.id,
                    is_deleted=False,
                )
                if cessacao_relacionada
                else Insubsistencia.objects.none()
            )
            if queryset.exists():
                raise serializers.ValidationError(
                    "Esta cessação já possui uma insubsistência cadastrada."
                )

        return data
