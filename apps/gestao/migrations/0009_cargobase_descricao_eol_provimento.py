from django.db import migrations, models
from django.db.models import F


def popular_descricao_eol(apps, schema_editor):
    """Até aqui a descrição do EOL ficava só em `descricao_completa`."""
    cargo_base_model = apps.get_model("gestao", "CargoBase")
    cargo_base_model.objects.update(descricao_eol=F("descricao_completa"))


class Migration(migrations.Migration):

    dependencies = [
        ("gestao", "0008_cargobase_data_fim_periodo_and_more"),
    ]

    operations = [
        migrations.AddField(
            model_name="cargobase",
            name="descricao_eol",
            field=models.CharField(
                default="",
                max_length=255,
                verbose_name="Descrição no EOL",
            ),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name="cargobase",
            name="provimento",
            field=models.TextField(
                blank=True, default="", verbose_name="Provimento"
            ),
        ),
        migrations.RunPython(
            popular_descricao_eol, migrations.RunPython.noop
        ),
    ]
