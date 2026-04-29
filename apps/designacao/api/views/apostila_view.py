from rest_framework import mixins, viewsets, status
from rest_framework.response import Response
from django.core.exceptions import ValidationError

from apps.designacao.models.apostila import Apostila
from apps.designacao.api.serializers.apostila_serializer import ApostilaSerializer
from apps.designacao.services.apostila_service import ApostilaService


class ApostilaViewSet(
    mixins.CreateModelMixin,
    mixins.ListModelMixin,
    mixins.RetrieveModelMixin,
    viewsets.GenericViewSet
):

    serializer_class = ApostilaSerializer

    def get_queryset(self):
        return Apostila.objects.filter(
            is_deleted=False
        ).select_related(
            "designacao",
            "cessacao"
        ).order_by("-criado_em")

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        try:
            apostila = ApostilaService.criar_apostila(serializer.validated_data)
        except ValidationError as e:
            return Response(
                {"detail": str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )

        return Response(
            ApostilaSerializer(apostila).data,
            status=status.HTTP_201_CREATED
        )