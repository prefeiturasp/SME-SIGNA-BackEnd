from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from .models import User


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    ordering = ["id"]
    list_display = ["id", "email", "name", "is_active", "is_staff"]
    search_fields = ["email", "name"]
    readonly_fields = ("last_login",)
