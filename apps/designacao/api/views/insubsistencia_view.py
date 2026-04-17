from rest_framework import mixins, viewsets 
from apps.designacao.models.insubsistencia import Insubsistencia
from apps.designacao.api.serializers.insubsistencia_serializer import InsubsistenciaSerializer

 
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