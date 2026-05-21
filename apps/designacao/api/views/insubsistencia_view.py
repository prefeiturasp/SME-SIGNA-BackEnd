from environ import logger
from rest_framework import mixins, status, viewsets
from rest_framework.exceptions import ValidationError
from rest_framework.response import Response

from apps.designacao.api.serializers.insubsistencia_serializer import (
    InsubsistenciaSerializer,
)
from apps.designacao.api.serializers.utils import extrair_mensagem_erro
from apps.designacao.models.insubsistencia import (
    Insubsistencia,
    TipoInsubsistencia,
)
from apps.designacao.services.insubsistencia_service import (
    InsubsistenciaService,
)


class InsubsistenciaViewSet(
    mixins.CreateModelMixin,
    mixins.ListModelMixin,
    mixins.RetrieveModelMixin,
    viewsets.GenericViewSet,
):
    serializer_class = InsubsistenciaSerializer

    def get_queryset(self):
        return (
            Insubsistencia.objects.filter(is_deleted=False)
            .select_related("designacao", "cessacao")
            .order_by("-criado_em")
        )

    def create(self, request, *args, **kwargs):
        try:
            serializer = self.get_serializer(data=request.data)
            serializer.is_valid(raise_exception=True)

            tipo = serializer.validated_data.get("tipo_insubsistencia")

            if tipo == TipoInsubsistencia.DESIGNACAO:
                InsubsistenciaService.montar_dados_insubsistencia_designacao(
                    serializer
                )
            else:
                InsubsistenciaService.montar_dados_insubsistencia_cessacao(
                    serializer
                )

            serializer.validated_data.pop("tipo_insubsistencia", None)

            self.perform_create(serializer)
            return Response(serializer.data, status=status.HTTP_201_CREATED)

        except ValidationError as e:
            return Response(
                {"detail": extrair_mensagem_erro(e.detail)}, status=400
            )
        except Exception as e:
            logger.error(f"Erro ao criar insubsistência: {e}")
            return Response({"detail": "Erro interno ao salvar."}, status=500)
