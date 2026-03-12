from rest_framework import serializers
from apps.designacao.models.designacao import Designacao 

class DesignacaoSerializer(serializers.ModelSerializer):
    impedimento_display = serializers.CharField(source='get_impedimento_substituicao_display', read_only=True)
    tipo_vaga_display = serializers.CharField(source='get_tipo_vaga_display', read_only=True)
    cargo_vaga_display = serializers.CharField(source='get_cargo_vaga_display', read_only=True)

    class Meta:
        model = Designacao
        fields = '__all__'