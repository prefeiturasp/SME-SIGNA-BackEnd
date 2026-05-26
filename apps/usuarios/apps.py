"""Configuração do app de usuários.

Define os metadados do Django para o aplicativo de usuários.
"""

from django.apps import AppConfig


class UsuariosConfig(AppConfig):
    """Configuração do aplicativo de usuários."""
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.usuarios'
    label = 'usuarios'
