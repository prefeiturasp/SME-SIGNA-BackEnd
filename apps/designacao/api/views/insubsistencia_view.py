from environ import logger
from rest_framework import mixins, serializers, status, viewsets 
from apps.designacao.models.designacao import Designacao
from apps.designacao.models.insubsistencia import Insubsistencia, TipoInsubsistencia
from apps.designacao.api.serializers.insubsistencia_serializer import InsubsistenciaSerializer
from rest_framework.response import Response
from apps.designacao.services.insubsistencia_service import InsubsistenciaService
 
class InsubsistenciaViewSet(
    mixins.CreateModelMixin,
    mixins.ListModelMixin,
    mixins.RetrieveModelMixin,
    viewsets.GenericViewSet
):
    serializer_class = InsubsistenciaSerializer
 
    def get_queryset(self):
        return Insubsistencia.objects.filter(
            is_deleted=False
        ).select_related(
            'designacao'
        ).order_by('-criado_em')
    
    def create(self, request, *args, **kwargs):

        try:
            serializer = self.get_serializer(data=request.data)

            serializer.is_valid(raise_exception=True)
            tipo_insubsistencia = serializer.validated_data.get('tipo_insubsistencia')
            
            if tipo_insubsistencia == TipoInsubsistencia.DESIGNACAO:
                self._criar_insubsistencia_designacao(serializer)

            elif tipo_insubsistencia == TipoInsubsistencia.CESSACAO:
                self._criar_insubsistencia_cessacao(serializer)
                
        except Exception as e:
            logger.error(f"Erro ao criar insubsistência: {e}")
            return Response(
                {"detail": str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )

        
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    def _criar_insubsistencia_designacao(self, serializer):  
        serializer_designacao=InsubsistenciaService.montar_dados_insubsistencia_designacao(serializer)
        self.perform_create(serializer_designacao)



    def _criar_insubsistencia_cessacao(self, serializer):  
        serializer_cessacao=InsubsistenciaService.montar_dados_insubsistencia_cessacao(serializer)
        self.perform_create(serializer_cessacao)

 
