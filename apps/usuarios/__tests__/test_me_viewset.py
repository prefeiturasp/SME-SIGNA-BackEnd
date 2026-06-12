"""Testes da view de informações do usuário autenticado.

Este módulo valida o endpoint /me para garantir que usuários
autenticados recebam os dados corretos de perfil.
"""

import secrets

import pytest

from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework.test import APIClient

User = get_user_model()


@pytest.mark.django_db
def test_me_view_authenticated_user_returns_user_data():
    """Verifica que usuário autenticado recebe seus dados de perfil."""
    client = APIClient()
    password = secrets.token_urlsafe(16)

    user = User.objects.create_user(
        username="teste",
        password=password,
        email="teste@email.com",
        name="Usuário Teste",
        cpf="12345678900",
    )

    client.force_authenticate(user=user)

    url = reverse("me")
    response = client.get(url)

    assert response.status_code == 200
    assert response.data == {
        "username": "teste",
        "name": "Usuário Teste",
        "email": "teste@email.com",
        "cpf": "12345678900",
    }
