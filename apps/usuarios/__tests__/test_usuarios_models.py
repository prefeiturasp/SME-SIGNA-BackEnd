"""Testes de unidade para o modelo de usuário.

Este módulo valida a criação de usuários, a representação em string
(@str) e a persistência segura de senhas no modelo de usuário.
"""

import secrets

import pytest

from django.contrib.auth import get_user_model

User = get_user_model()


@pytest.mark.django_db
def test_user_creation():
    """Verifica a criação de um usuário válido.

    Garante que um usuário é criado com ID, e-mail, nome e senha hash corretamente.
    """
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
    """Verifica a representação em string do usuário.

    Garante que o método __str__ retorna o nome de usuário esperado.
    """
    password = secrets.token_urlsafe(16)

    user = User.objects.create_user(username="testeuser", password=password)

    assert str(user) == "testeuser"


@pytest.mark.django_db
def test_password_is_hashed_on_save():
    """Verifica que a senha é armazenada de forma hash.

    Garante que a senha bruta não é persistida como texto simples e que
    o campo de senha usa um algoritmo de hash esperado.
    """
    raw_password = secrets.token_urlsafe(16)

    user = User(username="testeuser", password=raw_password)
    user.save()

    assert user.password != raw_password
    assert user.password.startswith("pbkdf2_sha256")
