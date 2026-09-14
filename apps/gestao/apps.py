"""Configuração do aplicativo de gestão.

Define a configuração do app `apps.gestao` para o projeto Django.
"""

from django.apps import AppConfig


class GestaoConfig(AppConfig):
    """Configuração da aplicação de gestão."""

    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.gestao"
