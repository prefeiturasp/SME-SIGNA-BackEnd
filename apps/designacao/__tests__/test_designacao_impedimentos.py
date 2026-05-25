from django.test import TestCase
from rest_framework.test import APIRequestFactory, force_authenticate
from unittest.mock import MagicMock
from apps.designacao.api.views.designacao_impedimentos_view import ImpedimentoSubstituicaoView
from apps.designacao.models.designacao import ImpedimentoSubstituicao

class TestImpedimentoSubstituicaoView(TestCase):

    def test_get_impedimento_substituicao_choices_success(self):
        ImpedimentoSubstituicao.objects.get_or_create(
            codigo='LIC_MEDICA',
            defaults={"descricao": "Por licença médica"}
        )
        ImpedimentoSubstituicao.objects.get_or_create(
            codigo='FERIAS',
            defaults={"descricao": "Por férias"}
        )

        factory = APIRequestFactory()
        request = factory.get('/qualquer-url/')

        user = MagicMock()
        force_authenticate(request, user=user)

        view = ImpedimentoSubstituicaoView.as_view()
        response = view(request)

        self.assertEqual(response.status_code, 200)

        expected_data = [
            {"value": 2, "label": "Por licença médica"},
            {"value": 4, "label": "Por férias"},
        ]

        for item in expected_data:
            self.assertIn(item, response.data)