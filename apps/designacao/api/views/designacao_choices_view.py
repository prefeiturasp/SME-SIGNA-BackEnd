from rest_framework.views import APIView
from rest_framework.response import Response
from apps.designacao.models import Designacao


class ImpedimentoSubstituicaoChoicesView(APIView):

    def get(self, request):
        choices = [
            {
                "value": value,
                "label": label
            }
            for value, label in Designacao.ImpedimentoSubstituicao.choices
        ]

        return Response(choices)