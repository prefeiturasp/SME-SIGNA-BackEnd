"""Serializadores para apostilas.

Define payloads de escrita e leitura de apostilas, incluindo alterações e
referência à insubsistência associada.
"""

from typing import Any

from rest_framework import serializers

from apps.designacao.api.serializers.ato_relacionado_mixin import (
    AtoRelacionadoMixin,
)
from apps.designacao.api.serializers.utils import NullableDateField
from apps.designacao.models.ato_administrativo import AtoAdministrativo


class ApostilaAlteracaoWriteSerializer(serializers.Serializer):
    """Serializador de alteração de apostila para entrada de dados."""

    campo_alterado = serializers.CharField(max_length=100)
    valor_novo = serializers.CharField()


class ApostilaWriteSerializer(serializers.Serializer):
    """Serializador de escrita para apostila.

    Valida os campos necessários para criar uma apostila vinculada a um ato
    pai.
    """

    ato_pai = serializers.PrimaryKeyRelatedField(
        queryset=AtoAdministrativo.objects.filter(
            tipo__in=[
                AtoAdministrativo.Tipo.DESIGNACAO,
                AtoAdministrativo.Tipo.CESSACAO,
            ]
        )
    )
    sei_numero = serializers.CharField(max_length=30)
    doc = NullableDateField(required=False, default=None, allow_null=True)
    observacao = serializers.CharField()
    alteracoes = ApostilaAlteracaoWriteSerializer(
        many=True, required=False, default=list
    )


class ApostilaAlteracaoReadSerializer(serializers.Serializer):
    """Serializador de leitura para alteração de apostila."""

    campo_alterado = serializers.CharField()
    valor_anterior = serializers.CharField()
    valor_novo = serializers.CharField()


class ApostilaReadSerializer(AtoRelacionadoMixin, serializers.ModelSerializer):
    """Serializador de leitura para apostila.

    Inclui o status do ato, observação, alterações e eventual insubsistência.
    """

    status = serializers.SerializerMethodField()
    observacao = serializers.CharField(
        source="apostila_detalhe.observacao", read_only=True
    )
    alteracoes = serializers.SerializerMethodField()
    insubsistencia = serializers.SerializerMethodField()

    designacao = serializers.SerializerMethodField()
    cessacao = serializers.SerializerMethodField()
    ato_apostilado = serializers.SerializerMethodField()
    ato_apostilado_display = serializers.SerializerMethodField()

    class Meta:
        model = AtoAdministrativo
        fields = [
            "id",
            "tipo",
            "status",
            "ato_pai_id",
            "sei_numero",
            "doc",
            "criado_em",
            "observacao",
            "alteracoes",
            "insubsistencia",
            "designacao",
            "cessacao",
            "ato_apostilado",
            "ato_apostilado_display",
            "numero_portaria",
        ]

    def get_status(self, obj: AtoAdministrativo) -> str:
        """Retorna o status do ato de apostila.

        Args:
            obj: Instância de AtoAdministrativo.

        Returns:
            str: Status do ato.

        """
        return obj.status

    def get_alteracoes(self, obj: AtoAdministrativo) -> Any:
        """Retorna as alterações registradas na apostila.

        Args:
            obj: Instância de AtoAdministrativo.

        Returns:
            list: Lista de alterações serializadas.

        """
        try:
            qs = obj.apostila_detalhe.alteracoes.all()
            return ApostilaAlteracaoReadSerializer(qs, many=True).data
        except Exception:
            return []

    def get_insubsistencia(self, obj: AtoAdministrativo) -> dict | None:
        """Retorna a insubsistência ativa associada à apostila.

        Args:
            obj: Instância de AtoAdministrativo.

        Returns:
            dict|None: Dados da insubsistência ou None se não houver.

        """
        insub = next(
            (
                f
                for f in obj.filhos.all()
                if f.tipo == AtoAdministrativo.Tipo.INSUBSISTENCIA
                and f.eh_valido
            ),
            None,
        )
        if not insub:
            return None
        try:
            d = insub.insubsistencia_detalhe
            return {
                "id": insub.id,
                "sei_numero": insub.sei_numero,
                "doc": insub.doc,
                "observacoes": d.observacoes,
                "criado_em": insub.criado_em,
            }
        except Exception:
            return None

    def get_tipo_de_ato(self, obj: AtoAdministrativo) -> str:
        """Retorna o tipo de ato em formato legível.

        Args:
            obj: Instância de AtoAdministrativo.

        Returns:
            str: Nome legível do tipo de ato.

        """
        if obj.ato_pai and obj.tipo != AtoAdministrativo.Tipo.CESSACAO:
            return (
                f"{obj.get_tipo_display()} de {obj.ato_pai.get_tipo_display()}"
            )
        return f"{obj.get_tipo_display()}"

    def get_ato_apostilado_display(self, obj: AtoAdministrativo) -> str | None:
        """Retorna o ato apostilado em formato legível.

        Args:
            obj: Instância de AtoAdministrativo.

        Returns:
            str: Tipo de ato apostilado.

        """
        if obj.ato_pai:
            return f"{obj.ato_pai.get_tipo_display()}"
        return None

    def get_ato_apostilado(self, obj: AtoAdministrativo) -> str | None:
        """Retorna o ato apostilado.

        Args:
            obj: Instância de AtoAdministrativo.

        Returns:
            str | None: Tipo de ato apostilado ou None se não aplicável.

        """
        if obj.ato_pai:
            return f"{obj.ato_pai.tipo}"
        return None
