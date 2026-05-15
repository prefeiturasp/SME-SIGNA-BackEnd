from rest_framework import serializers

from apps.designacao.models.ato_administrativo import AtoAdministrativo
from apps.designacao.api.serializers.utils import validar_somente_numeros


class InsubsistenciaV2WriteSerializer(serializers.Serializer):

    ato_pai         = serializers.PrimaryKeyRelatedField(queryset=AtoAdministrativo.objects.all())
    numero_portaria = serializers.CharField(max_length=20)
    ano_vigente     = serializers.CharField(max_length=6)
    sei_numero      = serializers.CharField(max_length=30)
    doc             = serializers.CharField(max_length=100, required=False, default='')
    observacoes     = serializers.CharField(required=False, default='')

    def validate_numero_portaria(self, value):
        return validar_somente_numeros(value)

    def validate_ano_vigente(self, value):
        return validar_somente_numeros(value)


class InsubsistenciaV2ReadSerializer(serializers.ModelSerializer):

    status      = serializers.SerializerMethodField()
    observacoes = serializers.CharField(
        source='insubsistencia_detalhe.observacoes', read_only=True
    )

    class Meta:
        model = AtoAdministrativo
        fields = [
            'id', 'tipo', 'status', 'ato_pai_id',
            'numero_portaria', 'ano_vigente', 'sei_numero', 'doc', 'criado_em',
            'observacoes',
        ]

    def get_status(self, obj):
        return obj.status
