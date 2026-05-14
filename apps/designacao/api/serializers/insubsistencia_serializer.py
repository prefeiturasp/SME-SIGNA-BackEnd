from rest_framework import serializers

from apps.designacao.models.ato_administrativo import AtoAdministrativo
from apps.designacao.models.insubsistencia import Insubsistencia, TipoInsubsistencia
from apps.designacao.api.serializers.utils import validar_somente_numeros


# ── Legado ────────────────────────────────────────────────────────────────────

class InsubsistenciaSerializer(serializers.ModelSerializer):
    tipo_insubsistencia = serializers.ChoiceField(
        choices=TipoInsubsistencia.choices,
        write_only=True,
        required=True,
    )

    class Meta:
        model = Insubsistencia
        fields = '__all__'

    def validate_numero_portaria(self, value):
        return validar_somente_numeros(value)

    def validate_ano_vigente(self, value):
        return validar_somente_numeros(value)

    def create(self, validated_data):
        validated_data.pop('tipo_insubsistencia', None)
        return super().create(validated_data)

    def validate(self, data):
        from apps.designacao.models.designacao import Designacao
        designacao = data.get('designacao')
        tipo_insubsistencia = data.get('tipo_insubsistencia')

        if not designacao:
            raise serializers.ValidationError(
                "Informe uma designação ou cessação para cadastrar a insubsistência."
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
            designacao_obj = Designacao.objects.select_related('cessacao').filter(
                id=designacao.id,
                is_deleted=False,
            ).first()
            cessacao_relacionada = getattr(designacao_obj, 'cessacao', None)
            queryset = Insubsistencia.objects.filter(
                cessacao_id=cessacao_relacionada.id,
                is_deleted=False,
            ) if cessacao_relacionada else Insubsistencia.objects.none()
            if queryset.exists():
                raise serializers.ValidationError(
                    "Esta cessação já possui uma insubsistência cadastrada."
                )

        return data


# ── Escrita ───────────────────────────────────────────────────────────────────

class InsubsistenciaWriteSerializer(serializers.Serializer):

    # AtoAdministrativo
    ato_pai         = serializers.PrimaryKeyRelatedField(queryset=AtoAdministrativo.objects.all())
    numero_portaria = serializers.CharField(max_length=20)
    ano_vigente     = serializers.CharField(max_length=6)
    sei_numero      = serializers.CharField(max_length=30)
    doc             = serializers.CharField(max_length=100, required=False, default='')

    # InsubsistenciaDetalhe
    observacoes = serializers.CharField(required=False, default='')

    def validate_numero_portaria(self, value):
        return validar_somente_numeros(value)

    def validate_ano_vigente(self, value):
        return validar_somente_numeros(value)


# ── Leitura ───────────────────────────────────────────────────────────────────

class InsubsistenciaReadSerializer(serializers.ModelSerializer):

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
