"""Configuração do Sphinx para documentação do projeto SIGNA."""

import os
import sys

import django

sys.path.insert(0, os.path.abspath(".."))
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings.local")
django.setup()

project = "SIGNA"
author = "SME"
language = "pt_BR"

extensions = [
    "sphinx.ext.autodoc",
    "sphinx.ext.napoleon",
]

html_theme = "alabaster"
