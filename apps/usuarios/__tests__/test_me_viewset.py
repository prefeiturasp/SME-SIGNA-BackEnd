import pytest
import secrets
from django.urls import reverse
from rest_framework.test import APIClient
from django.contrib.auth import get_user_model

User = get_user_model()


@pytest.mark.django_db
def test_me_view_authenticated_user_returns_user_data():
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
