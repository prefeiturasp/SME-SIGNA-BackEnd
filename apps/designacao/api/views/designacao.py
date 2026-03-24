from rest_framework import mixins, viewsets
from apps.designacao.models.designacao import Designacao
from apps.designacao.api.serializers.designacao_serializer import DesignacaoSerializer

class DesignacaoViewSet(mixins.CreateModelMixin,
                        mixins.ListModelMixin,
                        mixins.RetrieveModelMixin,
                        viewsets.GenericViewSet):
    queryset = Designacao.objects.all()
    serializer_class = DesignacaoSerializer