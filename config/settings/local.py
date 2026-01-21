from . import base as base_settings
from .base import env

# Copia todas as configurações em MAIÚSCULO para este módulo
for name in dir(base_settings):
    if name.isupper():
        globals()[name] = getattr(base_settings, name)

# Sobrescreva o que for diferente no ambiente local
DEBUG = True

# EMAIL
# ------------------------------------------------------------------------------
# https://docs.djangoproject.com/en/dev/ref/settings/#email-backend
EMAIL_BACKEND = env(
    "DJANGO_EMAIL_BACKEND", default="django.core.mail.backends.console.EmailBackend",
)


# Exemplo:
# INSTALLED_APPS += ["debug_toolbar"]
# MIDDLEWARE = ["debug_toolbar.middleware.DebugToolbarMiddleware", *MIDDLEWARE]
