"""Converte numero_portaria de texto para inteiro.

O campo era CharField e acumulou dois formatos: "005" (só dígitos) e
"005/2024" (número e ano no mesmo campo, com o ano também presente em
ano_vigente). Apostila nunca usou o campo e ficou com string vazia.

A conversão acontece em três passos porque o Postgres não consegue fazer
cast de "" nem de "005/2024" para integer:

1. permite NULL na coluna de texto;
2. normaliza os dados — descarta a barra e transforma "" em NULL;
3. troca o tipo para IntegerField.

O passo 2 recusa a migration, antes de alterar qualquer linha, diante de
qualquer valor que não seja convertível — seja por não caber em um integer,
seja por não ser numérico. As duas recusas existem porque as alternativas
são piores: sem a primeira, o passo 3 morre com um NumericValueOutOfRange
que não identifica nenhum registro; sem a segunda, um valor como "005-A"
viraria NULL em silêncio, perdendo o dado.

A única conversão silenciosa é "" para NULL, que é o caso conhecido da
apostila — ela nunca usou o campo.
"""

from django.db import migrations, models

# Teto do tipo integer (int4) do Postgres.
INTEGER_MAX = 2_147_483_647


def _descrever(registros):
    """Formata uma amostra de registros para a mensagem de erro.

    Args:
        registros: Lista de tuplas (pk, valor).

    Returns:
        str: Amostra de até dez registros, com contagem do excedente.

    """
    amostra = ", ".join(
        f"id={pk} numero_portaria={valor!r}" for pk, valor in registros[:10]
    )
    if len(registros) > 10:
        amostra += f" (e mais {len(registros) - 10})"
    return amostra


def _recusar_se_houver_valor_inconvertivel(ato_model):
    """Aborta a migration se algum valor não puder virar inteiro.

    A checagem roda antes de qualquer escrita para que a migration falhe
    apontando os registros culpados e sem deixar o banco em estado
    intermediário. Cobre dois casos:

    - número acima do teto do integer, que estouraria no ALTER COLUMN com
      uma mensagem que não identifica nenhuma linha;
    - valor não numérico, que seria convertido em NULL silenciosamente e
      perderia a informação.

    Args:
        ato_model: Modelo histórico usado pela migration.

    Raises:
        ValueError: Quando houver valor fora da faixa ou não numérico.

    """
    grandes = []
    invalidos = []

    for ato in ato_model.objects.all().iterator(chunk_size=2000):
        bruto = (ato.numero_portaria or "").strip()
        if not bruto:
            continue

        numero = bruto.partition("/")[0].strip()
        if not numero.isdecimal():
            invalidos.append((ato.pk, ato.numero_portaria))
        elif int(numero) > INTEGER_MAX:
            grandes.append((ato.pk, ato.numero_portaria))

    problemas = []
    if grandes:
        problemas.append(
            f"{len(grandes)} registro(s) acima de {INTEGER_MAX}, que não "
            f"cabem em um IntegerField: {_descrever(grandes)}"
        )
    if invalidos:
        problemas.append(
            f"{len(invalidos)} registro(s) com valor não numérico, que "
            f"seriam perdidos na conversão: {_descrever(invalidos)}"
        )

    if not problemas:
        return

    raise ValueError(
        "numero_portaria tem valores que não podem virar inteiro. "
        + " | ".join(problemas)
        + ". Corrija ou remova esses registros antes de aplicar esta "
        "migration — nenhuma linha foi alterada."
    )


def normalizar(apps, schema_editor):
    """Normaliza numero_portaria para conter apenas dígitos ou NULL.

    Registros no formato "NNN/AAAA" perdem a parte do ano. O ano só é
    gravado em ano_vigente quando esse campo ainda estiver vazio — quando
    já houver valor, ele é considerado a fonte da verdade e a barra é
    simplesmente descartada.

    Args:
        apps: Registry de modelos históricos da migration.
        schema_editor: Editor de schema da conexão em uso.

    """
    ato_model = apps.get_model("designacao", "AtoAdministrativo")

    _recusar_se_houver_valor_inconvertivel(ato_model)

    lote = []
    for ato in ato_model.objects.all().iterator(chunk_size=2000):
        bruto = (ato.numero_portaria or "").strip()
        numero, _, ano = bruto.partition("/")
        numero = numero.strip()
        ano = ano.strip()

        novo_numero = numero or None
        novo_ano = ato.ano_vigente
        if ano and not (ato.ano_vigente or "").strip():
            novo_ano = ano

        # Só toca em quem realmente muda: a maioria das linhas já está
        # limpa e reescrevê-las custa caro em tabela grande.
        if novo_numero == ato.numero_portaria and novo_ano == ato.ano_vigente:
            continue

        ato.numero_portaria = novo_numero
        ato.ano_vigente = novo_ano
        lote.append(ato)

        if len(lote) >= 2000:
            ato_model.objects.bulk_update(
                lote, ["numero_portaria", "ano_vigente"]
            )
            lote.clear()

    if lote:
        ato_model.objects.bulk_update(lote, ["numero_portaria", "ano_vigente"])


def reverter(apps, schema_editor):
    """Reverte a normalização.

    Não há como recuperar o formato "NNN/AAAA" original, então a reversão
    apenas devolve NULL para string vazia, mantendo a coluna utilizável.

    Args:
        apps: Registry de modelos históricos da migration.
        schema_editor: Editor de schema da conexão em uso.

    """
    ato_model = apps.get_model("designacao", "AtoAdministrativo")
    ato_model.objects.filter(numero_portaria=None).update(numero_portaria="")


class Migration(migrations.Migration):
    """Converte numero_portaria de CharField para IntegerField."""

    dependencies = [
        ("designacao", "0021_atoadministrativo_texto_sei_modelo_portaria"),
    ]

    operations = [
        migrations.AlterField(
            model_name="atoadministrativo",
            name="numero_portaria",
            field=models.CharField(
                max_length=20, blank=True, null=True, default=""
            ),
        ),
        migrations.RunPython(normalizar, reverter),
        migrations.AlterField(
            model_name="atoadministrativo",
            name="numero_portaria",
            field=models.IntegerField(blank=True, null=True),
        ),
    ]
