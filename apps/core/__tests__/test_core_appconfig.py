import pytest
from django.apps import apps

@pytest.mark.django_db
def test_core_app_config_registrado():
    # Recupera a AppConfig pelo label (normalmente o último segmento do path do app)
    app_config = apps.get_app_config("core")
    assert app_config is not None

def test_core_app_config_atributos():
    app_config = apps.get_app_config("core")
    # Confere o caminho do app
    assert app_config.name == "apps.core"
    # Confere o default_auto_field
    assert getattr(app_config, "default_auto_field", None) == "django.db.models.BigAutoField"