"""Views para a listagem de portarias.

Fornece endpoints para filtrar e atualizar portarias exibidas na publicação do
D.O.
"""

from django.db.models import QuerySet
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import filters, mixins, viewsets
from rest_framework import serializers as drf_serializers
from rest_framework.decorators import action
from rest_framework.request import Request
from rest_framework.response import Response

from apps.designacao.api.filters.portaria_filter import PortariaFilter
from apps.designacao.api.serializers.portaria_serializer import (
    PortariaListSerializer,
)
from apps.designacao.models.ato_administrativo import AtoAdministrativo


class PortariaListViewSet(mixins.ListModelMixin, viewsets.GenericViewSet):
    """ViewSet para listagem de portarias.

    Exibe portarias de Designação, Cessação, Insubsistência e Apostila
    conforme a tela de publicação do D.O.
    """

    serializer_class = PortariaListSerializer
    pagination_class = None

    filter_backends = [
        DjangoFilterBackend,
        filters.SearchFilter,
        filters.OrderingFilter,
    ]
    filterset_class = PortariaFilter

    search_fields = [
        "numero_portaria",
        "sei_numero",
        "designacao_detalhe__indicado_nome_servidor",
        "designacao_detalhe__indicado_nome_civil",
        "designacao_detalhe__indicado_rf",
    ]

    ordering_fields = [
        "numero_portaria",
        "ano_vigente",
        "criado_em",
    ]

    ordering = ["numero_portaria"]

    def get_queryset(self) -> QuerySet:
        """Retorna o queryset base de portarias.

        Returns:
            QuerySet: Atos administrativos com joins necessários para
            exibição de portarias.

        """
        resp = AtoAdministrativo.objects.select_related(
            "designacao_detalhe",
            "cessacao_detalhe",
            "insubsistencia_detalhe",
            "apostila_detalhe",
            "ato_pai__designacao_detalhe",
            "ato_raiz__designacao_detalhe",
            "ato_pai__cessacao_detalhe",
            "ato_pai__apostila_detalhe",
        ).order_by("numero_portaria")

        return resp

    @action(
        detail=False, methods=["post"], url_path="atualizar-data-publicacao"
    )
    def atualizar_data_publicacao(self, request: Request) -> Response:
        """Atualiza a data de publicação de portarias selecionadas.

        Args:
            request: Requisição HTTP contendo os IDs dos atos e a data de
            publicação.

        Returns:
            Response: Confirmação da atualização ou detalhes do erro.

        Raises:
            ValidationError: Se os campos obrigatórios não estiverem
            presentes ou se nenhum ato for encontrado.

        """
        ids = request.data.get("ids", [])
        data_publicacao = request.data.get("data_publicacao", "")

        if not ids:
            raise drf_serializers.ValidationError(
                {"ids": "Este campo é obrigatório."}
            )
        if not data_publicacao:
            raise drf_serializers.ValidationError(
                {"data_publicacao": "Este campo é obrigatório."}
            )

        updated = AtoAdministrativo.objects.filter(pk__in=ids).update(
            doc=data_publicacao,
            status_publicacao=AtoAdministrativo.StatusPublicacao.PUBLICADO,
        )

        if not updated:
            raise drf_serializers.ValidationError(
                {"ids": "Nenhum ato encontrado com os IDs informados."}
            )

        return Response(
            {
                "detail": f"{updated} ato(s) atualizado(s) com sucesso.",
                "ids": ids,
                "data_publicacao": data_publicacao,
            }
        )
