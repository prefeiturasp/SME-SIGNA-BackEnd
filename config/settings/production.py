from . import base as base_settings

for name in dir(base_settings):
    if name.isupper():
        globals()[name] = getattr(base_settings, name)
