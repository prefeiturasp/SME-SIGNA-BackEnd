from django.db import migrations

#Migration para atualizar ou criar cargos base iniciais.
CARGOS = [
    (
        "3085",
        "ASSISTENTE DE DIRETOR DE ESCOLA",
        "Assistente de Diretor de Escola",
    ),
    ("3360", "DIRETOR DE ESCOLA", "Diretor de Escola"),
    (
        "3379",
        "COORDENADOR PEDAGOGICO",
        "Coordenador Pedagógico",
    ),
    ("3182", "SECRETARIO DE ESCOLA", "Secretário de Escola"),
    ("3352", "SUPERVISOR ESCOLAR", "Supervisor Escolar"),
]


def corrigir_cargos_base(apps, schema_editor):
    cargo_base_model = apps.get_model("gestao", "CargoBase")

    for codigo, descricao_completa, _descricao_resumida in CARGOS:
        cargo_base_model.objects.filter(codigo_cargo=codigo).update(
            descricao_completa=descricao_completa,
            status="ATIVO",
            utilizado_para_designacoes=True,
        )


class Migration(migrations.Migration):

    dependencies = [
        ("gestao", "0007_populate_cargos_base_designacao"),
    ]

    operations = [
        migrations.RunPython(corrigir_cargos_base, migrations.RunPython.noop),
    ]
