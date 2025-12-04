import pytest
from django.contrib.auth import get_user_model

User = get_user_model()

TEST_PASSWORD = "senha_teste_123"
RAW_PASSWORD = "senha_raw_123"


@pytest.mark.django_db
def test_user_creation():
    user = User.objects.create_user(
        username="testeuser",
        password=TEST_PASSWORD,
        email="teste@example.com",
        name="Usuário Teste",
    )

    assert user.id is not None
    assert user.email == "teste@example.com"
    assert user.name == "Usuário Teste"
    assert user.check_password(TEST_PASSWORD)


@pytest.mark.django_db
def test_user_str():
    user = User.objects.create_user(
        username="testeuser",
        password=TEST_PASSWORD,
    )
    assert str(user) == "testeuser"


@pytest.mark.django_db
def test_password_is_hashed_on_save():
    user = User(username="testeuser", password=RAW_PASSWORD)
    user.save()

    assert user.password != RAW_PASSWORD
    assert user.password.startswith("pbkdf2_sha256")
