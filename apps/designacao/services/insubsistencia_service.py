from rest_framework.exceptions import ValidationError
from apps.designacao.models.designacao import Designacao
from apps.designacao.models.insubsistencia import Insubsistencia


class InsubsistenciaService:

    @staticmethod
    def montar_dados_insubsistencia_designacao(serializer):
        return serializer

    @staticmethod
    def montar_dados_insubsistencia_cessacao(serializer):
        designacao_obj = serializer.validated_data.get('designacao')

        designacao_completa = Designacao.objects.select_related('cessacao').get(id=designacao_obj.id, is_deleted=False)
        cessacao_obj = getattr(designacao_completa, 'cessacao', None)

        if not cessacao_obj:
            raise ValidationError("Cessação não encontrada para esta designação.")

        serializer.validated_data['cessacao'] = cessacao_obj
        serializer.validated_data['designacao'] = None 

        return serializer
    
    @staticmethod
    def criar_insubsistencia_designacao(data):
        designacao_id = data.get('designacao')
        
        designacao_obj = Designacao.objects.filter(id=designacao_id, is_deleted=False).first()
        
        if not designacao_obj:
            raise ValidationError("Designação não encontrada.")

        if Insubsistencia.objects.filter(designacao=designacao_obj, is_deleted=False).exists():
            raise ValidationError("Já existe uma insubsistência ativa para esta designação.")

        return Insubsistencia.objects.create(**data)