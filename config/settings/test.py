from . import base as base_settings  # ou local as base_settings, se preferir

# Copia todas as variáveis em MAIÚSCULAS do base_settings para este módulo
for name in dir(base_settings):
    if name.isupper():
        globals()[name] = getattr(base_settings, name)

# Agora sobrescreve apenas o que você quer para testes:
DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": ":memory:",
    }
}
