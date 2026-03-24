from django.db import migrations


def populate_impedimentos(apps, schema_editor):
    impedimento_model = apps.get_model('designacao', 'ImpedimentoSubstituicao')

    dados = [
        ('LIC_GESTANTE', 'Por licença gestante'),
        ('LIC_MEDICA', 'Por licença médica'),
        ('LIC_PATERNIDADE', 'Por licença paternidade'),
        ('FERIAS', 'Por férias'),
        ('LIC_MAT_ESP', 'Por licença maternidade especial'),
        ('LIC_ADOCAO', 'Por licença adoção'),
        ('LIC_GUARDA', 'Por licença guarda de menor'),
        ('MANDATO_ELETIVO', 'Para concorrer a mandato eletivo (Portaria 20/SEGES/2024)'),
        ('LIC_NOJO', 'Por licença nojo'),
        ('LIC_GALA', 'Por licença gala'),
        ('AFAST_CURSOS', 'Por afastamento Por Cursos/Congressos/Competições'),
        ('LIC_MATERNIDADE', 'Por licença maternidade'),
        ('PRORROG_GESTANTE', 'Por prorrogação da licença à gestante'),
        ('PARENTAL_CURTA', 'Por licença parental de curta duração'),
        ('PARENTAL_LONGA', 'Por licença parental de longa duração'),
        ('EVENTO_REUNIAO', 'Por Evento/Reunião'),
        ('READAPT_FUNC', 'Por readaptação funcional (Art. 39 Lei 8.979/79)'),
        ('SERV_TEC_A', 'Para prestar serviços técnico-educacionais (Art. 66, IX, a)'),
        ('CARGO_COMISSAO', 'Por exercer cargos em comissão (Art. 45 Lei 8.989/79)'),
        ('SERV_TEC_B', 'Para prestar serviços técnico-educacionais (Art. 66, IX, b)'),
        ('TRANSF_TEMP', 'Por transferência temporária (Decreto 57.444/16)'),
        ('DIRIGENTE_SINDICAL', 'Por exercer mandato de dirigente sindical'),
        ('AFAST_EXCEP', 'Pelo afastamento excepcional (Art. 66, IX, b)'),
    ]

    for codigo, descricao in dados:
        impedimento_model.objects.get_or_create(
            codigo=codigo,
            defaults={"descricao": descricao}
        )


def reverse_func(apps, schema_editor):
    impedimento_model = apps.get_model('designacao', 'ImpedimentoSubstituicao')
    impedimento_model.objects.all().delete()


class Migration(migrations.Migration):

    dependencies = [
        ('designacao', '0002_impedimentosubstituicao_and_more'),
    ]

    operations = [
        migrations.RunPython(populate_impedimentos, reverse_func),
    ]