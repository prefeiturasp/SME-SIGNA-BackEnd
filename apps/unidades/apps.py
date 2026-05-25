"""Configuração do aplicativo de unidades.

Este módulo define a configuração do Django para o aplicativo de unidades,
informando o nome do app e o tipo padrão para campos de chave primária.
"""

from django.apps import AppConfig


class UnidadesConfig(AppConfig):
    """Configurações do aplicativo de unidades.

    O AppConfig especifica o nome do aplicativo e o campo automático padrão
    para chaves primárias.
    """

    default_auto_field = 'django.db.models.BigAutoField'
    name = 'unidades'
