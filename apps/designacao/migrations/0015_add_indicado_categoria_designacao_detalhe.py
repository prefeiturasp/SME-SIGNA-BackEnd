from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("designacao", "0014_atoadministrativo_doc_charfield_to_datefield"),
    ]

    operations = [
        migrations.AddField(
            model_name="designacaodetalhe",
            name="indicado_categoria",
            field=models.CharField(blank=True, default="", max_length=255),
        ),
    ]
