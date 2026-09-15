# Generated manually (makemigrations não pôde ser usado por causa de um
# drift interativo não relacionado, pendente em outro app).

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ("gestao", "0006_alter_modeloportaria_options"),
        ("designacao", "0020_remove_cessacao_designacao_and_more"),
    ]

    operations = [
        migrations.AddField(
            model_name="atoadministrativo",
            name="texto_sei",
            field=models.TextField(blank=True, default=""),
        ),
        migrations.AddField(
            model_name="atoadministrativo",
            name="modelo_portaria",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.PROTECT,
                related_name="atos_gerados",
                to="gestao.modeloportaria",
            ),
        ),
    ]
