from django.test import TestCase
from rest_framework.test import APIRequestFactory, force_authenticate
from unittest.mock import patch, MagicMock
from apps.designacao.api.views.designacao_choices_view import ImpedimentoSubstituicaoChoicesView
from apps.designacao.models import Designacao

class TestImpedimentoSubstituicaoChoicesView(TestCase):

    @patch('apps.designacao.models.Designacao.ImpedimentoSubstituicao')
    def test_get_impedimento_substituicao_choices_success(self, mock_choices_enum):
        mock_choices_enum.choices = [
            ('valor_1', 'Label 1'),
            ('valor_2', 'Label 2'),
        ]

        factory = APIRequestFactory()
        request = factory.get('/qualquer-url/')
        
        user = MagicMock()
        force_authenticate(request, user=user)

        view = ImpedimentoSubstituicaoChoicesView.as_view()
        response = view(request)

        self.assertEqual(response.status_code, 200)
        expected_data = [
            {"value": "valor_1", "label": "Label 1"},
            {"value": "valor_2", "label": "Label 2"}
        ]
        self.assertEqual(response.data, expected_data)