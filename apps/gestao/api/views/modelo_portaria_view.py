"""Views para a API de modelos de portaria.

Fornece endpoints para listagem, criação e consulta de modelos de
texto de portaria cadastrados.
"""

from typing import Any

from django.db.models import QuerySet
from django_filters.rest_framework import DjangoFilterBackend
from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import (
    OpenApiParameter,
    OpenApiResponse,
    extend_schema,
)
from rest_framework import mixins, status, viewsets
from rest_framework.exceptions import ValidationError
from rest_framework.pagination import PageNumberPagination
from rest_framework.permissions import IsAuthenticated
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.gestao.api.filters.modelo_portaria_filter import ModeloPortariaFilter
from apps.gestao.api.serializers.modelo_portaria_serializer import (
    ModeloPortariaReadSerializer,
    ModeloPortariaWriteSerializer,
    VariavelModeloPortariaSerializer,
)
from apps.gestao.models.modelo_portaria import ModeloPortaria
from apps.gestao.services.modelo_portaria_service import ModeloPortariaService


class ModeloPortariaPagination(PageNumberPagination):
    """Paginação padrão da API de modelos de portaria.

    Define paginação baseada em número de página com tamanho padrão
    de 10 registros por página, permitindo customização via parâmetro
    `page_size` limitado ao máximo de 100 itens.
    """

    page_size = 10
    page_size_query_param = "page_size"
    max_page_size = 100


class ModeloPortariaViewSet(
    mixins.ListModelMixin,
    mixins.RetrieveModelMixin,
    mixins.CreateModelMixin,
    viewsets.GenericViewSet,
):
    """ViewSet de modelos de portaria.

    Expõe operações de listagem (com filtros e paginação), consulta
    individual e criação de modelos de portaria.
    """

    serializer_class = ModeloPortariaReadSerializer
    pagination_class = ModeloPortariaPagination
    filter_backends = [DjangoFilterBackend]
    filterset_class = ModeloPortariaFilter

    def get_queryset(self) -> QuerySet[ModeloPortaria]:
        """Retorna o queryset de modelos de portaria para a view.

        Returns:
            QuerySet: Modelos de portaria cadastrados.

        """
        return ModeloPortariaService.listar()

    def create(self, request: Request, *args: Any, **kwargs: Any) -> Response:
        """Cria um novo modelo de portaria a partir dos dados enviados.

        Args:
            request: Requisição HTTP contendo os dados de criação.
            *args: Argumentos posicionais adicionais.
            **kwargs: Argumentos nomeados adicionais.

        Returns:
            Response: Resposta HTTP com os dados do modelo de portaria criado.

        """
        serializer = ModeloPortariaWriteSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        modelo = ModeloPortariaService.criar(serializer.validated_data)

        return Response(
            ModeloPortariaReadSerializer(modelo).data,
            status=status.HTTP_201_CREATED,
        )


class ModeloPortariaVariaveisView(APIView):
    """View que retorna as opções de variáveis de modelo de portaria.

    Usada para popular o campo de seleção múltipla de variáveis no
    cadastro de modelos de portaria.
    """

    permission_classes = [IsAuthenticated]

    @extend_schema(
        parameters=[
            OpenApiParameter(
                name="tipo_cargo",
                type=OpenApiTypes.STR,
                location=OpenApiParameter.QUERY,
                required=False,
                enum=[
                    valor
                    for valor, _rotulo in ModeloPortaria.TipoCargo.choices
                ],
                description=(
                    "Tipo de cargo do modelo. Restringe as variáveis que "
                    "só valem para um tipo de cargo — hoje `TITULAR` só é "
                    "devolvida com `CARGO_VAGO`. Sem o parâmetro, todas "
                    "as variáveis são devolvidas."
                ),
            ),
        ],
        responses={
            200: VariavelModeloPortariaSerializer(many=True),
            400: OpenApiResponse(
                description="`tipo_cargo` fora das opções aceitas."
            ),
        },
    )
    def get(self, request: Request) -> Response:
        """Retorna a lista de variáveis disponíveis para modelos de portaria.

        A lista depende do tipo de cargo informado em `tipo_cargo`: a
        variável `TITULAR` só é oferecida para `CARGO_VAGO`. Sem o
        parâmetro, todas as variáveis são devolvidas.

        Args:
            request: Requisição HTTP GET.

        Returns:
            Response: Lista de variáveis com `value` e `display_name`.

        Raises:
            ValidationError: Quando `tipo_cargo` não é uma opção válida.

        """
        tipo_cargo = self._tipo_cargo(request)
        variaveis = [
            {"value": valor, "display_name": rotulo}
            for valor, rotulo in ModeloPortaria.variaveis_disponiveis(
                tipo_cargo
            )
        ]
        return Response(
            VariavelModeloPortariaSerializer(variaveis, many=True).data,
            status=status.HTTP_200_OK,
        )

    @staticmethod
    def _tipo_cargo(request: Request) -> str | None:
        """Lê e valida o `tipo_cargo` da query string.

        Args:
            request: Requisição HTTP com o parâmetro opcional `tipo_cargo`.

        Returns:
            str|None: Tipo de cargo informado, ou None quando ausente.

        Raises:
            ValidationError: Quando o valor não é uma opção de
                `ModeloPortaria.TipoCargo`.

        """
        tipo_cargo = request.query_params.get("tipo_cargo") or None
        if tipo_cargo is None:
            return None
        if tipo_cargo not in ModeloPortaria.TipoCargo.values:
            raise ValidationError(
                {
                    "tipo_cargo": (
                        f"'{tipo_cargo}' não é um tipo de cargo válido."
                    )
                }
            )
        return tipo_cargo
