# Generated manually to add ModeloPortaria.tipo_ato_pai

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("gestao", "0004_modeloportaria"),
    ]

    operations = [
        migrations.AddField(
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
                null=True,
                blank=True,
                verbose_name="Tipo do ato pai",
            ),
        ),
    ]
