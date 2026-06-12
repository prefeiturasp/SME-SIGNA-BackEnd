from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("designacao", "0015_add_indicado_categoria_designacao_detalhe"),
    ]

    operations = [
        migrations.AlterField(
            model_name="designacaodetalhe",
            name="indicado_categoria",
            field=models.CharField(blank=True, default="", max_length=3),
        ),
    ]
