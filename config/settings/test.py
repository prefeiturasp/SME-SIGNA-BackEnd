# config/settings/test.py
from .local import *  # ou from .base import * (o que fizer sentido)

# Use SQLite em memória para testes
DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": ":memory:",  # ou BASE_DIR / "test_db.sqlite3"
    }
}