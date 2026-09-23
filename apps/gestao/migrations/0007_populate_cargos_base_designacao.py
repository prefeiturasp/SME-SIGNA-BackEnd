from django.db import migrations

# Cargos legados que antes eram um enum fixo em DesignacaoDetalhe.CargoVaga.
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


def popular_cargos_base(apps, schema_editor):
    cargo_base_model = apps.get_model("gestao", "CargoBase")

    for codigo, descricao_completa, descricao_resumida in CARGOS:
        cargo_base_model.objects.get_or_create(
            codigo_cargo=codigo,
            defaults={
                "descricao_completa": descricao_completa,
                "descricao_resumida": descricao_resumida,
                "grupamento": "GESTORES_EDUCACAO",
                "situacao_funcional": "EFETIVO",
                "status": "ATIVO",
                "utilizado_para_designacoes": True,
            },
        )


def reverse_func(apps, schema_editor):
    cargo_base_model = apps.get_model("gestao", "CargoBase")
    codigos = [codigo for codigo, _, _ in CARGOS]
    cargo_base_model.objects.filter(codigo_cargo__in=codigos).delete()


class Migration(migrations.Migration):

    dependencies = [
        ("gestao", "0006_alter_modeloportaria_options"),
    ]

    operations = [
        migrations.RunPython(popular_cargos_base, reverse_func),
    ]
