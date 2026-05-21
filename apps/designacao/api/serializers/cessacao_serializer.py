from rest_framework import serializers

from apps.designacao.api.serializers.insubsistencia_serializer import (
    InsubsistenciaSerializer,
)
from apps.designacao.api.serializers.utils import validar_somente_numeros
from apps.designacao.models.cessacao import Cessacao


class CessacaoSerializer(serializers.ModelSerializer):
    insubsistencia = serializers.SerializerMethodField()

    class Meta:
        model = Cessacao
        fields = "__all__"

    def get_insubsistencia(self, obj):

        insubsistencia = (
            obj.insubsistencia.filter(is_deleted=False)
            .order_by("-criado_em")
            .first()
        )
        if insubsistencia and not insubsistencia.is_deleted:
            return InsubsistenciaSerializer(insubsistencia).data

        return None

    def validate_numero_portaria(self, value):
        return validar_somente_numeros(value)

    def validate_ano_vigente(self, value):
        return validar_somente_numeros(value)

    def validate(self, data):
        designacao = data.get("designacao")

        if designacao and hasattr(designacao, "cessacao"):
            raise serializers.ValidationError(
                "Esta designação já possui uma cessação cadastrada."
            )

        return data
