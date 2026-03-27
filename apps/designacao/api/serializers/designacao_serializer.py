from rest_framework import serializers
from apps.designacao.models.designacao import Designacao, ImpedimentoSubstituicao
class ImpedimentoSubstituicaoSerializer(serializers.ModelSerializer):
    class Meta:
        model = ImpedimentoSubstituicao
        fields = ['id', 'codigo', 'descricao']


class DesignacaoSerializer(serializers.ModelSerializer):
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

    def get_field_names(self, declared_fields, info):
        fields = super().get_field_names(declared_fields, info)
        return fields + ['impedimento_substituicao_detail', 'tipo_vaga_display', 'cargo_vaga_display']