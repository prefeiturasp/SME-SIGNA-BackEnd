from rest_framework import serializers

from apps.designacao.api.serializers.apostila_serializer import (
    ApostilaSerializer,
)
from apps.designacao.api.serializers.cessacao_serializer import (
    CessacaoSerializer,
)
from apps.designacao.api.serializers.insubsistencia_serializer import (
    InsubsistenciaSerializer,
)
from apps.designacao.models.designacao import (
    Designacao,
    ImpedimentoSubstituicao,
)


class ImpedimentoSubstituicaoLegadoSerializer(serializers.ModelSerializer):
    class Meta:
        model = ImpedimentoSubstituicao
        fields = ["id", "codigo", "descricao"]


class DesignacaoLegadoSerializer(serializers.ModelSerializer):

    cessacao = serializers.SerializerMethodField()
    insubsistencia = serializers.SerializerMethodField()
    apostilas = serializers.SerializerMethodField()

    # Campos opcionais que o model não declara blank=True mas o frontend não envia
    ue = serializers.CharField(
        max_length=50, required=False, default="", allow_blank=True
    )
    dre = serializers.CharField(
        max_length=50, required=False, default="", allow_blank=True
    )
    funcionarios_da_unidade = serializers.CharField(
        max_length=50, required=False, default="", allow_blank=True
    )
    doc = serializers.CharField(
        max_length=100, required=False, default="", allow_blank=True
    )

    impedimento_substituicao = serializers.PrimaryKeyRelatedField(
        queryset=ImpedimentoSubstituicao.objects.all(),
        required=False,
        allow_null=True,
    )
    impedimento_substituicao_detail = ImpedimentoSubstituicaoLegadoSerializer(
        source="impedimento_substituicao",
        read_only=True,
    )
    impedimento_display = serializers.SerializerMethodField()

    tipo_vaga_display = serializers.CharField(
        source="get_tipo_vaga_display", read_only=True
    )
    cargo_vaga_display = serializers.CharField(
        source="get_cargo_vaga_display", read_only=True
    )

    class Meta:
        model = Designacao
        fields = "__all__"

    def get_cessacao(self, obj):
        try:
            cessacao = obj.cessacao
            if cessacao and not cessacao.is_deleted:
                return CessacaoSerializer(cessacao).data
        except Exception:
            pass
        return None

    def get_insubsistencia(self, obj):
        insubsistencia = (
            obj.insubsistencia.filter(is_deleted=False)
            .order_by("-criado_em")
            .first()
        )
        if insubsistencia:
            return InsubsistenciaSerializer(insubsistencia).data
        return None

    def get_apostilas(self, obj):
        apostilas = obj.apostilas.filter(is_deleted=False).order_by(
            "-criado_em"
        )
        return ApostilaSerializer(apostilas, many=True).data

    def get_impedimento_display(self, obj):
        if obj.impedimento_substituicao:
            return obj.impedimento_substituicao.descricao
        return None

    def update(self, instance, validated_data):
        for field in ("is_deleted", "deleted_at", "criado_em", "id"):
            validated_data.pop(field, None)
        return super().update(instance, validated_data)
