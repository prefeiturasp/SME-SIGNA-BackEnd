"""Configuração de administração do Django para o modelo de usuário.

Este módulo registra o modelo de usuário personalizado no admin do Django
com ordenação, exibição e campos de pesquisa configurados.
"""

from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from .models import User


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    """Personaliza a interface de administração para o modelo User.

    Configura a ordenação padrão, os campos exibidos na lista, os campos
    pesquisáveis e os campos somente leitura no admin.
    """
    ordering = ["id"]
    list_display = ["id", "email", "name", "is_active", "is_staff"]
    search_fields = ["email", "name"]
    readonly_fields = ("last_login",)
