import pytest
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase
from unittest.mock import patch
from django.contrib.auth import get_user_model

class TestImpedimentoSubstituicaoChoicesView(APITestCase):

    @patch('apps.designacao.models.Designacao.ImpedimentoSubstituicao')
    def test_get_impedimento_substituicao_choices_success(self, mock_choices_enum):
        User = get_user_model()
        user = User.objects.create_user(username='testuser')
        self.client.force_authenticate(user=user)

        mock_choices_enum.choices = [
            ('valor_1', 'Label 1'),
            ('valor_2', 'Label 2'),
        ]

        url = '/api/designacao/designacoes/impedimentos/'
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        expected_data = [
            {"value": "valor_1", "label": "Label 1"},
            {"value": "valor_2", "label": "Label 2"}
        ]
        self.assertEqual(response.json(), expected_data)