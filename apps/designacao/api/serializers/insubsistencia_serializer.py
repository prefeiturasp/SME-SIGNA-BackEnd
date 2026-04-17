from rest_framework import serializers
from apps.designacao.api.serializers.utils import validar_somente_numeros
from apps.designacao.models.designacao import Designacao
from apps.designacao.models.insubsistencia import Insubsistencia


class InsubsistenciaSerializer(serializers.ModelSerializer):

    class Meta:
        model = Insubsistencia
        fields = '__all__'
 

    def validate_numero_portaria(self, value):
        return validar_somente_numeros(value)

    def validate_ano_vigente(self, value):
        return validar_somente_numeros(value)

    def validate_sei_numero(self, value):
        return validar_somente_numeros(value)

    def validate(self, data):
        designacao = data.get('designacao')
        cessacao = data.get('cessacao')
   
        if not designacao and not cessacao:
            raise serializers.ValidationError(
                "Informe uma designação ou cessação para cadastrar a insubsistência."
            )

        if designacao:
            queryset = Insubsistencia.objects.filter(
                designacao=designacao,
                is_deleted=False,
            )
 
            if queryset.exists():
                raise serializers.ValidationError(
                    "Esta designação já possui uma insubsistência cadastrada."
                )        
        
        if cessacao:
            queryset = Insubsistencia.objects.filter(
                cessacao_id=cessacao,   
                is_deleted=False,
            )
 
            if queryset.exists():
                raise serializers.ValidationError(
                    "Esta cessação já possui uma insubsistência cadastrada."
                )

        


        if designacao:

            queryset = Designacao.objects.filter(
                id=designacao.id,
                is_deleted=False,
            ).select_related('cessacao')

            designacao_obj = queryset.first()         
            
            cessacao_relacionada = getattr(designacao_obj, 'cessacao', None)
 
            cessacao_sem_insubsistencia = (
                not cessacao_relacionada
                or not Insubsistencia.objects.filter(
                    cessacao_id=cessacao_relacionada.id,
                    is_deleted=False,
                ).exists()
            )

            if (
                cessacao_relacionada
                and not cessacao_relacionada.is_deleted
                and cessacao_sem_insubsistencia
            ):
                data['cessacao'] = cessacao_relacionada
                
 

        return data