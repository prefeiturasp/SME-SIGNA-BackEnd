from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ("designacao", "0017_atoadministrativo_status_publicacao"),
    ]

    operations = [
        migrations.CreateModel(
            name="InsubsistenciaApostilaDetalhe",
            fields=[
                (
                    "ato",
                    models.OneToOneField(
                        on_delete=django.db.models.deletion.CASCADE,
                        primary_key=True,
                        related_name="insubsistencia_apostila_detalhe",
                        serialize=False,
                        to="designacao.atoadministrativo",
                    ),
                ),
                ("texto", models.TextField(blank=True, default="")),
            ],
            options={
                "db_table": "insubsistencia_apostila_detalhe",
            },
        ),
    ]
