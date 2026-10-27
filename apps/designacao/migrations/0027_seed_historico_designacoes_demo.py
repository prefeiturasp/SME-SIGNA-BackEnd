"""Dados de demonstração do histórico de designações (opt-in).

Esta migração existe para carregar, em um passo, os cenários de
designação, cessação, apostila e insubsistência usados para testar o
endpoint ``/api/designacao/historico-de-designacoes/<codigo_ue>/``.

Ela **só cria dados** quando a variável de ambiente
``SEED_HISTORICO_DESIGNACOES`` está ligada: assim a suíte de testes e o
banco de qualquer outro ambiente não ganham registros fictícios.
Formas de carregar:

    # 1) Aplicando esta migração com a variável ligada
    SEED_HISTORICO_DESIGNACOES=1 python manage.py migrate designacao

    # 2) Comando idempotente (pode rodar quantas vezes quiser)
    python manage.py seed_historico_demo

Para remover:

    python manage.py seed_historico_demo --apagar
    # ou: python manage.py migrate designacao 0026
"""

import os

from django.db import migrations

from apps.designacao.seed.historico_demo import (
    VARIAVEL_AMBIENTE,
    apagar_dados_demo,
    criar_dados_demo,
)

_VALORES_LIGADOS = {"1", "true", "t", "yes", "y", "sim", "s"}


def _seed_ligado() -> bool:
    """Indica se o seed foi habilitado por variável de ambiente."""
    valor = os.environ.get(VARIAVEL_AMBIENTE, "")
    return valor.strip().lower() in _VALORES_LIGADOS


def criar_dados_demonstracao(apps, schema_editor):
    """Cria os cenários de demonstração quando habilitado."""
    if not _seed_ligado():
        return
    criar_dados_demo()


def remover_dados_demonstracao(apps, schema_editor):
    """Remove os cenários de demonstração (rollback)."""
    apagar_dados_demo()


class Migration(migrations.Migration):

    dependencies = [
        ("designacao", "0026_index_designacao_detalhe_ue"),
    ]

    operations = [
        migrations.RunPython(
            criar_dados_demonstracao, remover_dados_demonstracao
        ),
    ]
