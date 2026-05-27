"""Views para a API de apostilas.

Fornece endpoints para criar, listar e recuperar apostilas.
"""

from rest_framework import mixins, status, viewsets
from rest_framework.exceptions import ValidationError
from rest_framework.response import Response

from apps.designacao.api.serializers.apostila_serializer import ApostilaSerializer
from apps.designacao.models.apostila import Apostila
from apps.designacao.services.apostila_service import ApostilaService


class ApostilaViewSet(
    mixins.CreateModelMixin,
    mixins.ListModelMixin,
    mixins.RetrieveModelMixin,
    viewsets.GenericViewSet,
):
    """ViewSet de apostila.

    Permite criar novas apostilas, listar apostilas existentes e recuperar
    detalhes de uma apostila específica.
    """

    serializer_class = ApostilaSerializer

    def get_queryset(self):
        """Retorna o queryset de apostilas ativas.

        Returns:
            QuerySet: Apostilas não deletadas ordenadas por data de criação.
        """
        return (
            Apostila.objects.filter(is_deleted=False)
            .select_related("designacao", "cessacao")
            .order_by("-criado_em")
        )

    def create(self, request, *args, **kwargs):
        """Cria uma nova apostila a partir dos dados da requisição.

        Args:
            request: Requisição HTTP contendo os dados da apostila.
            *args: Argumentos posicionais adicionais.
            **kwargs: Argumentos nomeados adicionais.

        Returns:
            Response: Resposta HTTP com os dados da apostila criada ou
            erro de validação.
        """
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        try:
            apostila = ApostilaService.criar_apostila(serializer.validated_data)

        except ValidationError as e:
            if isinstance(e.detail, list):
                message = e.detail[0]
            elif isinstance(e.detail, dict):
                message = next(iter(e.detail.values()))[0]
            else:
                message = str(e.detail)

            return Response({"detail": message}, status=status.HTTP_400_BAD_REQUEST)

        return Response(
            ApostilaSerializer(apostila).data, status=status.HTTP_201_CREATED
        )
