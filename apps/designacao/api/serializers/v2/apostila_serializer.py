from rest_framework import serializers

from apps.designacao.models.ato_administrativo import AtoAdministrativo
from apps.designacao.api.serializers.utils import NullableDateField


class ApostilaV2AlteracaoWriteSerializer(serializers.Serializer):
    campo_alterado = serializers.CharField(max_length=100)
    valor_novo = serializers.CharField()


class ApostilaV2WriteSerializer(serializers.Serializer):

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
    alteracoes = ApostilaV2AlteracaoWriteSerializer(
        many=True, required=False, default=list
    )


class ApostilaV2AlteracaoReadSerializer(serializers.Serializer):
    campo_alterado = serializers.CharField()
    valor_anterior = serializers.CharField()
    valor_novo = serializers.CharField()


class ApostilaV2ReadSerializer(serializers.ModelSerializer):

    status = serializers.SerializerMethodField()
    observacao = serializers.CharField(
        source="apostila_detalhe.observacao", read_only=True
    )
    alteracoes = serializers.SerializerMethodField()
    insubsistencia = serializers.SerializerMethodField()

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
        ]

    def get_status(self, obj):
        return obj.status

    def get_alteracoes(self, obj):
        try:
            qs = obj.apostila_detalhe.alteracoes.all()
            return ApostilaV2AlteracaoReadSerializer(qs, many=True).data
        except Exception:
            return []

    def get_insubsistencia(self, obj):
        insub = next(
            (
                f
                for f in obj.filhos.all()
                if f.tipo == AtoAdministrativo.Tipo.INSUBSISTENCIA and f.eh_valido
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
