from rest_framework.response import Response
from rest_framework.views import APIView

from apps.designacao.models import ImpedimentoSubstituicao


class ImpedimentoSubstituicaoView(APIView):

    def get(self, request):
        impedimentos = ImpedimentoSubstituicao.objects.all()

        data = [{"value": i.id, "label": i.descricao} for i in impedimentos]

        return Response(data)
