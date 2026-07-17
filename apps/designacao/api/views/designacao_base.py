"""Base compartilhada entre views de designação.

Contém a paginação comum e os helpers de controle de paginação/filtros
usados por DesignacaoViewSet.
"""

from typing import Any

from django.db.models import QuerySet
from rest_framework.pagination import PageNumberPagination
from rest_framework.request import Request
from rest_framework.views import APIView

_PAGINATION_PARAMS = {"page", "page_size", "format", "no_pagination"}


class DesignacaoBasePagination(PageNumberPagination):
    """Paginação base que suporta desabilitar via no_pagination=true."""

    page_size = 10
    page_size_query_param = "page_size"
    max_page_size = 100

    def paginate_queryset(
        self,
        queryset: QuerySet,
        request: Request,
        view: APIView | None = None,
    ) -> list | None:
        """Decide se a paginação deve ser aplicada.

        Args:
            queryset: Queryset a ser paginado.
            request: Requisição HTTP.
            view: View atual.

        Returns:
            list|None: Lista paginada ou None quando a paginação está
            desabilitada.

        """
        if request.query_params.get("no_pagination", "").lower() == "true":
            return None
        return super().paginate_queryset(queryset, request, view)


class DesignacaoPaginacaoMixin:
    """Helpers de paginação compartilhados pelas views de designação."""

    # Anotação para que type checkers reconheçam que a view terá `request`
    request: Any

    def _is_no_pagination(self) -> bool:
        """Verifica se a paginação deve ser desabilitada.

        Returns:
            bool: True quando no_pagination=true estiver presente.

        """
        return (
            self.request.query_params.get("no_pagination", "").lower()
            == "true"
        )

    def _has_filters(self) -> bool:
        """Verifica se a requisição contém filtros além da paginação.

        Returns:
            bool: True quando houver parâmetros além dos de paginação.

        """
        return bool(set(self.request.query_params.keys()) - _PAGINATION_PARAMS)

    def _should_limit_queryset(self) -> bool:
        """Determina se o queryset deve ser limitado.

        Returns:
            bool: True quando não houver filtros nem desabilitação de
            paginação.

        """
        return not self._has_filters() and not self._is_no_pagination()
