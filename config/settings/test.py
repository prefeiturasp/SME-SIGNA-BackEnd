# config/settings/test.py
from . import local  # ou from . import base

# Use SQLite em memória para testes
DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": ":memory:",
    }
}