"""Serializadores v2 para apostilas.

Define payloads de escrita e leitura de apostilas, incluindo alterações e
referência à insubsistência associada.
"""

from rest_framework import serializers

from apps.designacao.models.ato_administrativo import AtoAdministrativo
from apps.designacao.api.serializers.utils import NullableDateField


class ApostilaV2AlteracaoWriteSerializer(serializers.Serializer):
    """Serializador de alteração de apostila para entrada de dados."""
    campo_alterado = serializers.CharField(max_length=100)
    valor_novo     = serializers.CharField()


class ApostilaV2WriteSerializer(serializers.Serializer):
    """Serializador de escrita para apostila v2.

    Valida os campos necessários para criar uma apostila vinculada a um ato pai.
    """

    ato_pai = serializers.PrimaryKeyRelatedField(
        queryset=AtoAdministrativo.objects.filter(
            tipo__in=[AtoAdministrativo.Tipo.DESIGNACAO, AtoAdministrativo.Tipo.CESSACAO]
        )
    )
    sei_numero = serializers.CharField(max_length=30)
    doc        = NullableDateField(required=False, default=None, allow_null=True)
    observacao = serializers.CharField()
    alteracoes = ApostilaV2AlteracaoWriteSerializer(many=True, required=False, default=list)


class ApostilaV2AlteracaoReadSerializer(serializers.Serializer):
    """Serializador de leitura para alteração de apostila."""
    campo_alterado = serializers.CharField()
    valor_anterior = serializers.CharField()
    valor_novo     = serializers.CharField()


class ApostilaV2ReadSerializer(serializers.ModelSerializer):
    """Serializador de leitura para apostila v2.

    Inclui o status do ato, observação, alterações e eventual insubsistência.
    """

    status     = serializers.SerializerMethodField()
    observacao = serializers.CharField(source='apostila_detalhe.observacao', read_only=True)
    alteracoes     = serializers.SerializerMethodField()
    insubsistencia = serializers.SerializerMethodField()

    class Meta:
        model = AtoAdministrativo
        fields = [
            'id', 'tipo', 'status', 'ato_pai_id',
            'sei_numero', 'doc', 'criado_em',
            'observacao', 'alteracoes', 'insubsistencia',
        ]

    def get_status(self, obj):
        """Retorna o status do ato de apostila.

        Args:
            obj: Instância de AtoAdministrativo.

        Returns:
            str: Status do ato.
        """
        return obj.status

    def get_alteracoes(self, obj):
        """Retorna as alterações registradas na apostila.

        Args:
            obj: Instância de AtoAdministrativo.

        Returns:
            list: Lista de alterações serializadas.
        """
        try:
            qs = obj.apostila_detalhe.alteracoes.all()
            return ApostilaV2AlteracaoReadSerializer(qs, many=True).data
        except Exception:
            return []

    def get_insubsistencia(self, obj):
        """Retorna a insubsistência ativa associada à apostila.

        Args:
            obj: Instância de AtoAdministrativo.

        Returns:
            dict|None: Dados da insubsistência ou None se não houver.
        """
        insub = next(
            (f for f in obj.filhos.all()
             if f.tipo == AtoAdministrativo.Tipo.INSUBSISTENCIA and f.eh_valido),
            None,
        )
        if not insub:
            return None
        try:
            d = insub.insubsistencia_detalhe
            return {
                'id': insub.id,
                'sei_numero': insub.sei_numero,
                'doc': insub.doc,
                'observacoes': d.observacoes,
                'criado_em': insub.criado_em,
            }
        except Exception:
            return None
