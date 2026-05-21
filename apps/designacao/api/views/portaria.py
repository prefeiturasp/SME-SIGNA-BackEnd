from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import filters, mixins
from rest_framework import serializers as drf_serializers
from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from apps.designacao.api.filters.portaria_filter import PortariaFilter
from apps.designacao.api.serializers.portaria_serializer import (
    PortariaListSerializer,
)
from apps.designacao.models.ato_administrativo import AtoAdministrativo


class PortariaListViewSet(mixins.ListModelMixin, viewsets.GenericViewSet):
    """
    ViewSet para listagem de portarias (Designação, Cessação,
    Insubsistência, Apostila) conforme tela de publicação no D.O.

    Colunas exibidas:
        PORTARIA | DOC | TIPO DE ATO | NOME | CARGO | D.O |
        DATA DA DESIGNAÇÃO | DATA DA CESSAÇÃO | Nº SEI
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

    def get_queryset(self):
        return AtoAdministrativo.objects.select_related(
            "designacao_detalhe",
            "cessacao_detalhe",
            "insubsistencia_detalhe",
            "apostila_detalhe",
            "ato_pai__designacao_detalhe",
            "ato_raiz__designacao_detalhe",
        ).order_by("numero_portaria")

    @action(
        detail=False, methods=["post"], url_path="atualizar-data-publicacao"
    )
    def atualizar_data_publicacao(self, request):
        """
        Atualiza o campo doc dos atos selecionados.

        Payload:
        {
            "ids": [1, 2, 3],
            "data_publicacao": "..."
        }
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

        updated = AtoAdministrativo.objects.filter(
            pk__in=ids, ativo=True
        ).update(doc=data_publicacao)

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
