from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("designacao", "0013_add_novos_campos_designacao_detalhe"),
    ]

    operations = [
        # 1. Torna nullable como CharField para poder setar NULL sem violar constraint
        migrations.AlterField(
            model_name="atoadministrativo",
            name="doc",
            field=models.CharField(max_length=100, blank=True, null=True),
        ),
        # 2. Limpa valores existentes (strings não podem ser convertidas para date)
        migrations.RunSQL(
            "UPDATE ato_administrativo SET doc = NULL",
            reverse_sql=migrations.RunSQL.noop,
        ),
        # 3. Converte para DateField
        migrations.AlterField(
            model_name="atoadministrativo",
            name="doc",
            field=models.DateField(blank=True, null=True),
        ),
    ]
