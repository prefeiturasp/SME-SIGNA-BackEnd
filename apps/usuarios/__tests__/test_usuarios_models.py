import pytest
import secrets
from django.contrib.auth import get_user_model

User = get_user_model()


@pytest.mark.django_db
def test_user_creation():
    password = secrets.token_urlsafe(16)

    user = User.objects.create_user(
        username="testeuser",
        password=password,
        email="teste@example.com",
        name="Usuário Teste",
    )

    assert user.id is not None
    assert user.email == "teste@example.com"
    assert user.name == "Usuário Teste"
    assert user.check_password(password)


@pytest.mark.django_db
def test_user_str():
    password = secrets.token_urlsafe(16)

    user = User.objects.create_user(
        username="testeuser",
        password=password
    )

    assert str(user) == "testeuser"


@pytest.mark.django_db
def test_password_is_hashed_on_save():
    raw_password = secrets.token_urlsafe(16)

    user = User(username="testeuser", password=raw_password)
    user.save()

    assert user.password != raw_password
    assert user.password.startswith("pbkdf2_sha256")
