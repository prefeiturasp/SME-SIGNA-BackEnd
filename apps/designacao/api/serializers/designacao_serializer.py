from rest_framework import serializers
from apps.designacao.api.serializers.insubsistencia_serializer import InsubsistenciaSerializer
from apps.designacao.models.designacao import Designacao, ImpedimentoSubstituicao
from apps.designacao.api.serializers.cessacao_serializer import CessacaoSerializer



class ImpedimentoSubstituicaoSerializer(serializers.ModelSerializer):
    class Meta:
        model = ImpedimentoSubstituicao
        fields = ['id', 'codigo', 'descricao']


class DesignacaoSerializer(serializers.ModelSerializer):
    cessacao = serializers.SerializerMethodField()
    insubsistencia = serializers.SerializerMethodField()
    impedimento_display = serializers.SerializerMethodField()

    impedimento_substituicao_detail = ImpedimentoSubstituicaoSerializer(
        source='impedimento_substituicao',
        read_only=True
    )

    impedimento_substituicao = serializers.PrimaryKeyRelatedField(
        queryset=ImpedimentoSubstituicao.objects.all(),
        required=False,
        allow_null=True
    )

    tipo_vaga_display = serializers.CharField(source='get_tipo_vaga_display', read_only=True)
    cargo_vaga_display = serializers.CharField(source='get_cargo_vaga_display', read_only=True)

    class Meta:
        model = Designacao
        fields = '__all__'
        
    def get_insubsistencia(self, obj):
        try:
            insubsistencia = obj.insubsistencia.filter(is_deleted=False).order_by('-criado_em').first()
            if insubsistencia and not insubsistencia.is_deleted:
                return InsubsistenciaSerializer(insubsistencia).data
        except Exception: 
            pass
        return None

    def get_cessacao(self, obj):
        try:
            cessacao = obj.cessacao
            if cessacao and not cessacao.is_deleted:
                return CessacaoSerializer(cessacao).data
        except Exception: 
            pass
        return None

    def get_impedimento_display(self, obj):
        if obj.impedimento_substituicao:
            return obj.impedimento_substituicao.descricao
        return None

    def update(self, instance, validated_data):
        protected_fields = ['is_deleted', 'deleted_at', 'criado_em', 'id']

        for field in protected_fields:
            validated_data.pop(field, None)

        return super().update(instance, validated_data)