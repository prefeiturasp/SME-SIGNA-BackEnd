"""Configuração do aplicativo de alteração de e-mail.

Este módulo define a configuração do Django para o aplicativo
`alteracao_email`, incluindo o campo automático padrão para chaves primárias.
"""

from django.apps import AppConfig


class AlteracaoEmailConfig(AppConfig):
    """Configurações do aplicativo de alteração de e-mail.

    O AppConfig identifica o nome do aplicativo Django e o tipo padrão para
    campos de chave primária.
    """

    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.alteracao_email'
