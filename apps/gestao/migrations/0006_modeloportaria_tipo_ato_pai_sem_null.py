# Generated manually to fix python:S6553 (avoid null=True on CharField)

from django.db import migrations, models


def preencher_tipo_ato_pai_vazio(apps, schema_editor):
    ModeloPortaria = apps.get_model("gestao", "ModeloPortaria")
    ModeloPortaria.objects.filter(tipo_ato_pai__isnull=True).update(
        tipo_ato_pai=""
    )


class Migration(migrations.Migration):

    dependencies = [
        ("gestao", "0005_modeloportaria_tipo_ato_pai"),
    ]

    operations = [
        migrations.RunPython(
            preencher_tipo_ato_pai_vazio, migrations.RunPython.noop
        ),
        migrations.AlterField(
            model_name="modeloportaria",
            name="tipo_ato_pai",
            field=models.CharField(
                choices=[
                    ("DESIGNACAO", "Designação"),
                    ("CESSACAO", "Cessação"),
                    ("APOSTILA", "Apostila"),
                    ("INSUBSISTENCIA", "Insubsistência"),
                ],
                max_length=20,
                blank=True,
                default="",
                verbose_name="Tipo do ato pai",
            ),
        ),
    ]
