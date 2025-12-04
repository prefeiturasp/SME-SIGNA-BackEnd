from . import base as base_settings

# Copia todas as configurações em MAIÚSCULO para este módulo
for name in dir(base_settings):
    if name.isupper():
        globals()[name] = getattr(base_settings, name)

# Sobrescreva o que for diferente no ambiente local
DEBUG = True

# Exemplo:
# INSTALLED_APPS += ["debug_toolbar"]
# MIDDLEWARE = ["debug_toolbar.middleware.DebugToolbarMiddleware", *MIDDLEWARE]
