"""Views para a API de cargos base.

Fornece endpoints para listagem, criação e consulta de cargos base
cadastrados, além do proxy de cargos do EOL usado no início do cadastro.
"""

import logging
from typing import Any

from django.db.models import QuerySet
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import mixins, status, viewsets
from rest_framework.pagination import PageNumberPagination
from rest_framework.permissions import IsAuthenticated
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.gestao.api.filters.cargo_base_filter import CargoBaseFilter
from apps.gestao.api.serializers.cargo_base_serializer import (
    CargoBaseReadSerializer,
    CargoBaseUpdateSerializer,
    CargoBaseWriteSerializer,
)
from apps.gestao.models.cargo_base import CargoBase
from apps.gestao.services.cargo_base_service import CargoBaseService
from apps.helpers.exceptions import SmeIntegracaoError
from apps.usuarios.services.sme_integracao_service import SmeIntegracaoService

logger = logging.getLogger(__name__)


class CargoBasePagination(PageNumberPagination):
    """Paginação padrão da API de cargos base.

    Define paginação baseada em número de página com tamanho padrão
    de 10 registros por página, permitindo customização via parâmetro
    `page_size` limitado ao máximo de 100 itens.
    """

    page_size = 10
    page_size_query_param = "page_size"
    max_page_size = 100


class CargoBaseViewSet(
    mixins.ListModelMixin,
    mixins.CreateModelMixin,
    viewsets.GenericViewSet,
):
    """ViewSet de cargos base.

    Expõe operações de listagem (com filtros e paginação) e criação de
    cargos base.
    """

    serializer_class = CargoBaseReadSerializer
    pagination_class = CargoBasePagination
    filter_backends = [DjangoFilterBackend]
    filterset_class = CargoBaseFilter

    def get_queryset(self) -> QuerySet[CargoBase]:
        """Retorna o queryset de cargos base para a view.

        Returns:
            QuerySet: Cargos base cadastrados.

        """
        return CargoBaseService.listar()

    def create(self, request: Request, *args: Any, **kwargs: Any) -> Response:
        """Cria um novo cargo base a partir dos dados enviados.

        Args:
            request: Requisição HTTP contendo os dados de criação.
            *args: Argumentos posicionais adicionais.
            **kwargs: Argumentos nomeados adicionais.

        Returns:
            Response: Resposta HTTP com os dados do cargo base criado.

        """
        serializer = CargoBaseWriteSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        cargo = CargoBaseService.criar(serializer.validated_data)

        return Response(
            CargoBaseReadSerializer(cargo).data,
            status=status.HTTP_201_CREATED,
        )

    def partial_update(
        self, request: Request, *args: Any, **kwargs: Any
    ) -> Response:
        """Atualiza parcialmente um cargo base existente.

        Args:
            request: Requisição HTTP contendo os campos a atualizar.
            *args: Argumentos posicionais adicionais.
            **kwargs: Argumentos nomeados adicionais.

        Returns:
            Response: Resposta HTTP com os dados atualizados do cargo base.

        """
        cargo = self.get_object()
        serializer = CargoBaseUpdateSerializer(
            cargo, data=request.data, partial=True
        )
        serializer.is_valid(raise_exception=True)

        cargo = CargoBaseService.atualizar(cargo, serializer.validated_data)

        return Response(CargoBaseReadSerializer(cargo).data)


class CargoEolView(APIView):
    """View que retorna a lista de cargos cadastrados no EOL.

    Usada para selecionar o cargo de origem no início do cadastro de um
    cargo base.
    """

    permission_classes = [IsAuthenticated]

    def get(self, request: Request) -> Response:
        """Retorna a lista de cargos cadastrados no EOL.

        Args:
            request: Requisição HTTP GET.

        Returns:
            Response: Lista de cargos do EOL ou mensagem de erro.

        """
        try:
            cargos = SmeIntegracaoService.buscar_cargos()
            return Response(cargos, status=status.HTTP_200_OK)

        except SmeIntegracaoError as e:
            return Response(
                {"detail": str(e)}, status=status.HTTP_400_BAD_REQUEST
            )

        except Exception:
            logger.exception("Erro inesperado ao buscar cargos no EOL")
            return Response(
                {"detail": "Erro interno do servidor"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )
