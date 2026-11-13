from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("designacao", "0026_index_designacao_detalhe_ue"),
    ]

    operations = [
        migrations.AddField(
            model_name="designacaodetalhe",
            name="indicado_codigo_ue_cargo_base",
            field=models.CharField(blank=True, default="", max_length=50),
        ),
    ]
