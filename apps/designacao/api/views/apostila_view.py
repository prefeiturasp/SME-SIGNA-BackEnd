from rest_framework import mixins, status, viewsets
from rest_framework.exceptions import ValidationError
from rest_framework.response import Response

from apps.designacao.api.serializers.apostila_serializer import (
    ApostilaSerializer,
)
from apps.designacao.models.apostila import Apostila
from apps.designacao.services.apostila_service import ApostilaService


class ApostilaViewSet(
    mixins.CreateModelMixin,
    mixins.ListModelMixin,
    mixins.RetrieveModelMixin,
    viewsets.GenericViewSet,
):

    serializer_class = ApostilaSerializer

    def get_queryset(self):
        return (
            Apostila.objects.filter(is_deleted=False)
            .select_related("designacao", "cessacao")
            .order_by("-criado_em")
        )

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        try:
            apostila = ApostilaService.criar_apostila(
                serializer.validated_data
            )

        except ValidationError as e:
            if isinstance(e.detail, list):
                message = e.detail[0]
            elif isinstance(e.detail, dict):
                message = next(iter(e.detail.values()))[0]
            else:
                message = str(e.detail)

            return Response(
                {"detail": message}, status=status.HTTP_400_BAD_REQUEST
            )

        return Response(
            ApostilaSerializer(apostila).data, status=status.HTTP_201_CREATED
        )
