"""Adiciona `ato_alterado` em ApostilaAlteracao.

Permite que uma apostila sobre uma cessação corrija também campos da
designação de origem, registrando explicitamente contra qual ato cada
alteração foi aplicada. Substitui a constraint única antiga
(`apostila`, `campo_alterado`), que assumia um único alvo por apostila,
por uma que também considera o ato alterado — evitando colisão quando o
mesmo nome de campo (ex.: `numero_portaria`) é corrigido tanto na
cessação quanto na designação dentro da mesma apostila.

Para os registros já existentes, `ato_alterado` é preenchido com o
`ato_pai` da própria apostila — que é exatamente o alvo implícito que
essas alterações sempre tiveram até aqui.
"""

import django.db.models.deletion
from django.db import migrations, models


def preencher_ato_alterado(apps, schema_editor):
    """Backfill: ato_alterado = ato_pai da apostila, para linhas antigas."""
    ApostilaAlteracao = apps.get_model("designacao", "ApostilaAlteracao")
    alteracoes = ApostilaAlteracao.objects.select_related(
        "apostila__ato"
    ).iterator()
    for alteracao in alteracoes:
        alteracao.ato_alterado_id = alteracao.apostila.ato.ato_pai_id
        alteracao.save(update_fields=["ato_alterado"])


def noop(apps, schema_editor):
    """Reversão: nada a fazer, a coluna é removida pela migração anterior."""


class Migration(migrations.Migration):

    dependencies = [
        ("designacao", "0021_atoadministrativo_texto_sei_modelo_portaria"),
    ]

    operations = [
        migrations.RemoveConstraint(
            model_name="apostilaalteracao",
            name="unique_campo_por_apostila",
        ),
        migrations.AddField(
            model_name="apostilaalteracao",
            name="ato_alterado",
            field=models.ForeignKey(
                null=True,
                on_delete=django.db.models.deletion.PROTECT,
                related_name="alteracoes_recebidas",
                to="designacao.atoadministrativo",
            ),
        ),
        migrations.RunPython(preencher_ato_alterado, noop),
        migrations.AlterField(
            model_name="apostilaalteracao",
            name="ato_alterado",
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.PROTECT,
                related_name="alteracoes_recebidas",
                to="designacao.atoadministrativo",
            ),
        ),
        migrations.AddConstraint(
            model_name="apostilaalteracao",
            constraint=models.UniqueConstraint(
                fields=["apostila", "ato_alterado", "campo_alterado"],
                name="unique_campo_por_apostila_e_ato",
            ),
        ),
    ]
