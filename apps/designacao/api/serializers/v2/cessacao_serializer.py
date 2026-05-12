from rest_framework import serializers

from apps.designacao.models.ato_administrativo import AtoAdministrativo
from apps.designacao.api.serializers.utils import validar_somente_numeros


class CessacaoV2WriteSerializer(serializers.Serializer):

    # AtoAdministrativo pai (designação à qual esta cessação pertence)
    ato_pai = serializers.PrimaryKeyRelatedField(
        queryset=AtoAdministrativo.objects.filter(tipo=AtoAdministrativo.Tipo.DESIGNACAO)
    )

    # Campos de AtoAdministrativo
    numero_portaria = serializers.CharField(max_length=20)
    ano_vigente     = serializers.CharField(max_length=6)
    sei_numero      = serializers.CharField(max_length=30)
    doc             = serializers.CharField(max_length=100, required=False, default='')

    # Campos de CessacaoDetalhe
    a_pedido      = serializers.BooleanField(required=False, default=False)
    remocao       = serializers.BooleanField(required=False, default=False)
    aposentadoria = serializers.BooleanField(required=False, default=False)
    data_cessacao = serializers.DateField()

    def validate_numero_portaria(self, value):
        return validar_somente_numeros(value)

    def validate_ano_vigente(self, value):
        return validar_somente_numeros(value)


class CessacaoV2ReadSerializer(serializers.ModelSerializer):

    # Campos do ato pai (designação)
    ato_pai_id = serializers.IntegerField(read_only=True)

    # Campos de CessacaoDetalhe
    a_pedido      = serializers.BooleanField(source='cessacao_detalhe.a_pedido',      read_only=True)
    remocao       = serializers.BooleanField(source='cessacao_detalhe.remocao',       read_only=True)
    aposentadoria = serializers.BooleanField(source='cessacao_detalhe.aposentadoria', read_only=True)
    data_cessacao = serializers.DateField(source='cessacao_detalhe.data_cessacao',    read_only=True)

    class Meta:
        model = AtoAdministrativo
        fields = [
            'id', 'tipo', 'status', 'ato_pai_id', 'ato_raiz_id',
            'numero_portaria', 'ano_vigente', 'sei_numero', 'doc', 'criado_em',
            'a_pedido', 'remocao', 'aposentadoria', 'data_cessacao',
        ]
