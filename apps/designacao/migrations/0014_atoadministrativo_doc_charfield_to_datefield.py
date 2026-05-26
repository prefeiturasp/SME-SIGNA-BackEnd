from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('designacao', '0013_add_novos_campos_designacao_detalhe'),
    ]

    operations = [
        migrations.RunSQL(
            "UPDATE ato_administrativo SET doc = NULL",
            reverse_sql=migrations.RunSQL.noop,
        ),
        migrations.AlterField(
            model_name='atoadministrativo',
            name='doc',
            field=models.DateField(blank=True, null=True),
        ),
    ]
