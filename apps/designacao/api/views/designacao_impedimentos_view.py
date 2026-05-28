"""View para listagem de impedimentos de substituição.

Fornece endpoint para retorno de valores e labels de impedimentos usados na UI.
"""

from rest_framework.response import Response
from rest_framework.views import APIView

from apps.designacao.models import ImpedimentoSubstituicao


class ImpedimentoSubstituicaoView(APIView):
    """View que retorna lista de impedimentos de substituição."""

    def get(self, request):
        """Recupera todos os impedimentos de substituição.

        Args:
            request: Requisição HTTP GET.

        Returns:
            Response: Lista de impedimentos com value/label.
        """
        impedimentos = ImpedimentoSubstituicao.objects.all()

        data = [{"value": i.id, "label": i.descricao} for i in impedimentos]

        return Response(data)
