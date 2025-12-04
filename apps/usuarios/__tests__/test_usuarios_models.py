import pytest
from django.contrib.auth import get_user_model

User = get_user_model()


@pytest.mark.django_db
def test_user_creation():
    user = User.objects.create_user(
        username="testeuser",
        password="minhasenha",
        email="teste@example.com",
        name="Usuário Teste"
    )
    assert user.id is not None
    assert user.email == "teste@example.com"
    assert user.name == "Usuário Teste"
    assert user.check_password("minhasenha")


@pytest.mark.django_db
def test_user_str():
    user = User.objects.create_user(
        username="testeuser",
        password="123456"
    )
    assert str(user) == "testeuser"


@pytest.mark.django_db
def test_password_is_hashed_on_save():
    user = User(username="testeuser", password="senha123")
    user.save()

    assert user.password != "senha123"
    assert user.password.startswith("pbkdf2_sha256")
