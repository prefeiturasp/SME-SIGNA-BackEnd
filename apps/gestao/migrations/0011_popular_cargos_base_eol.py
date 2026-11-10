"""Popula os cargos base a partir da planilha unificada de cargos do EOL.

Os dados estão em ``data/0011_cargos_base_eol.csv``, já convertidos para
os valores do modelo. O arquivo pertence a esta migration e não deve ser
editado: correções futuras entram em uma migration nova.

Regras:
- o código do cargo no EOL é a referência: cargos existentes são
  atualizados e os demais são criados;
- só os campos presentes no arquivo são gravados; ``status``,
  ``permite_substituicao``, ``possui_periodo_fechado`` e
  ``data_fim_periodo`` de cargos existentes não mudam;
- só os 5 cargos de gestão já usados na designação ficam com
  ``utilizado_para_designacoes``;
- o arquivo é validado por inteiro antes de gravar; qualquer erro
  interrompe a migration sem gravar nada.
"""

import csv
from pathlib import Path

from django.db import migrations

ARQUIVO = Path(__file__).resolve().parent / "data" / "0011_cargos_base_eol.csv"

CAMPOS_TEXTO = ("descricao_eol", "descricao_resumida", "descricao_completa")
CAMPOS_BOOLEANOS = (
    "testar_laudo",
    "utilizado_para_funcoes",
    "utilizado_para_designacoes",
    "utilizado_para_ste",
    "utilizado_para_permutas",
    "cargo_base_ficticio",
    "pesquisar_licencas_no_sigpec",
)
SIM_NAO = {"S": True, "N": False}


def ler_cargos(cargo_base_model) -> list[dict]:
    """Lê e valida o arquivo, devolvendo os dados prontos para gravar.

    Args:
        cargo_base_model: Modelo histórico de ``CargoBase``.

    Returns:
        list[dict]: Um dicionário por cargo, com os valores do modelo.

    Raises:
        ValueError: Com todos os erros encontrados no arquivo.

    """
    opcoes = {
        campo: {
            valor
            for valor, _ in cargo_base_model._meta.get_field(campo).choices
        }
        for campo in ("grupamento", "situacao_funcional")
    }
    tamanhos = {
        campo: cargo_base_model._meta.get_field(campo).max_length
        for campo in ("codigo_cargo", *CAMPOS_TEXTO)
    }

    with ARQUIVO.open(encoding="utf-8", newline="") as arquivo:
        linhas = list(csv.DictReader(arquivo))

    erros: list[str] = []
    cargos: list[dict] = []
    vistos: set[str] = set()
    for numero, linha in enumerate(linhas, start=2):
        codigo = linha["codigo_cargo"].strip()

        def erro(mensagem: str, codigo: str = codigo, numero: int = numero):
            erros.append(
                f"linha {numero} (código {codigo or '?'}): {mensagem}"
            )

        if not codigo.isdecimal():
            erro("código do cargo ausente ou não numérico")
        elif codigo in vistos:
            erro("código do cargo repetido")
        vistos.add(codigo)

        dados: dict = {"provimento": linha["provimento"].strip()}
        for campo, limite in tamanhos.items():
            valor = linha[campo].strip()
            if not valor:
                erro(f"{campo} vazio")
            elif len(valor) > limite:
                erro(f"{campo} com mais de {limite} caracteres")
            dados[campo] = valor

        for campo, validas in opcoes.items():
            valor = linha[campo].strip()
            if valor not in validas:
                erro(f"{campo} inválido: {valor!r}")
            dados[campo] = valor

        for campo in CAMPOS_BOOLEANOS:
            valor = linha[campo].strip()
            if valor not in SIM_NAO:
                erro(f"{campo} deve ser S ou N: {valor!r}")
            dados[campo] = SIM_NAO.get(valor, False)

        quantidade = linha["quantidade_maxima_de_dias_de_licenca"].strip()
        if not quantidade.isdecimal():
            erro("quantidade_maxima_de_dias_de_licenca deve ser inteiro")
            quantidade = "0"
        dados["quantidade_maxima_de_dias_de_licenca"] = int(quantidade)

        # Mesma regra do serializer: a pesquisa no SIGPEC exige uma
        # quantidade de dias maior que zero, e vice-versa.
        if dados["pesquisar_licencas_no_sigpec"] != bool(
            dados["quantidade_maxima_de_dias_de_licenca"]
        ):
            erro("pesquisa no SIGPEC e quantidade de dias incoerentes")

        cargos.append(dados)

    if erros:
        raise ValueError(
            "Arquivo de cargos base inválido:\n" + "\n".join(erros)
        )
    return cargos


def popular_cargos_base(apps, schema_editor):
    """Cria ou atualiza os cargos base pelo código do cargo no EOL."""
    cargo_base_model = apps.get_model("gestao", "CargoBase")
    for dados in ler_cargos(cargo_base_model):
        codigo = dados.pop("codigo_cargo")
        cargo_base_model.objects.update_or_create(
            codigo_cargo=codigo, defaults=dados
        )


class Migration(migrations.Migration):
    dependencies = [
        ("gestao", "0010_alter_cargobase_grupamento"),
    ]

    # Desfazer não apaga cargos: não há como saber quais já existiam ou
    # foram alterados pela tela depois do seed.
    operations = [
        migrations.RunPython(popular_cargos_base, migrations.RunPython.noop),
    ]
