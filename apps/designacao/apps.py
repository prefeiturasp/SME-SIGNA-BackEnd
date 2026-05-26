"""Configuração do aplicativo de designação.

Define a configuração do app `apps.designacao` para o projeto Django.
"""

from django.apps import AppConfig


class DesignacaoConfig(AppConfig):
    """Configuração da aplicação de designações."""

    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.designacao'
