"""Testes do seed de cargos base (migration 0011)."""

import csv
import importlib

import pytest
from django.apps import apps as django_apps

from apps.gestao.models.cargo_base import CargoBase

seed = importlib.import_module(
    "apps.gestao.migrations.0011_popular_cargos_base_eol"
)

CARGOS_GESTAO = {"3085", "3182", "3352", "3360", "3379"}


def _linhas_do_arquivo() -> list[dict]:
    with seed.ARQUIVO.open(encoding="utf-8", newline="") as arquivo:
        return list(csv.DictReader(arquivo))


def test_arquivo_versionado_e_valido():
    cargos = seed.ler_cargos(CargoBase)

    assert len(cargos) == 112
    assert all(c["codigo_cargo"].isdecimal() for c in cargos)


@pytest.mark.django_db
def test_banco_tem_todos_os_cargos_do_arquivo():
    codigos = {linha["codigo_cargo"] for linha in _linhas_do_arquivo()}

    assert codigos <= set(
        CargoBase.objects.values_list("codigo_cargo", flat=True)
    )


@pytest.mark.django_db
def test_so_os_cargos_de_gestao_sao_usados_em_designacao():
    codigos = {linha["codigo_cargo"] for linha in _linhas_do_arquivo()}
    em_designacao = set(
        CargoBase.objects.filter(
            codigo_cargo__in=codigos, utilizado_para_designacoes=True
        ).values_list("codigo_cargo", flat=True)
    )

    assert em_designacao == CARGOS_GESTAO


@pytest.mark.django_db
def test_cargo_existente_e_atualizado_pela_planilha():
    cargo = CargoBase.objects.get(codigo_cargo="3379")

    assert cargo.descricao_resumida == "CP"
    assert cargo.descricao_completa == "Coordenador Pedagógico"
    assert cargo.provimento == "experiência de 3 anos no Magistério"
    assert cargo.pesquisar_licencas_no_sigpec is True
    assert cargo.quantidade_maxima_de_dias_de_licenca == 30


@pytest.mark.django_db
def test_cargo_novo_com_grupamento_novo():
    cargo = CargoBase.objects.get(codigo_cargo="2655")

    assert cargo.grupamento == CargoBase.Grupamento.SAUDE
    assert cargo.situacao_funcional == CargoBase.SituacaoFuncional.EFETIVO
    assert cargo.utilizado_para_designacoes is False
    assert cargo.pesquisar_licencas_no_sigpec is False
    assert cargo.quantidade_maxima_de_dias_de_licenca == 0
    assert cargo.status == CargoBase.Status.ATIVO


@pytest.mark.django_db
@pytest.mark.parametrize(
    ("codigo", "resumida", "completa"),
    [
        (
            "2648",
            "Espec. Saúde - N II",
            "Especialista em Saúde - Nível II",
        ),
        (
            "2649",
            "Espec. Saúde - N III",
            "Especialista em Saúde - Nível III",
        ),
        (
            "5703",
            "Assist. de Suporte Operacional - Nível I",
            "Assistente de Suporte Operacional - Nível I",
        ),
        (
            "3247",
            "Prof Subs 1º Grau N I",
            "Professor Substituto de 1º Grau Nível I",
        ),
    ],
)
def test_erros_de_digitacao_corrigidos(codigo, resumida, completa):
    cargo = CargoBase.objects.get(codigo_cargo=codigo)

    assert cargo.descricao_resumida == resumida
    assert cargo.descricao_completa == completa


@pytest.mark.django_db
def test_comissionado_e_convertido():
    cargo = CargoBase.objects.get(codigo_cargo="3220")

    assert cargo.situacao_funcional == CargoBase.SituacaoFuncional.COMISSIONADO


@pytest.mark.django_db
def test_reaplicar_nao_altera_campos_fora_do_arquivo():
    CargoBase.objects.filter(codigo_cargo="3360").update(
        status=CargoBase.Status.INATIVO,
        permite_substituicao=True,
        descricao_resumida="Editado pela tela",
    )

    seed.popular_cargos_base(django_apps, None)

    cargo = CargoBase.objects.get(codigo_cargo="3360")
    assert cargo.status == CargoBase.Status.INATIVO
    assert cargo.permite_substituicao is True
    assert cargo.descricao_resumida == "Diretor de Escola"


def _escrever_arquivo(caminho, linhas: list[dict]) -> None:
    with caminho.open("w", encoding="utf-8", newline="") as arquivo:
        escritor = csv.DictWriter(arquivo, fieldnames=list(linhas[0]))
        escritor.writeheader()
        escritor.writerows(linhas)


@pytest.mark.django_db
@pytest.mark.parametrize(
    ("campo", "valor", "mensagem"),
    [
        ("codigo_cargo", "", "código do cargo ausente"),
        ("descricao_completa", " ", "descricao_completa vazio"),
        ("grupamento", "Saúde", "grupamento inválido"),
        ("situacao_funcional", "efetivo", "situacao_funcional inválido"),
        ("testar_laudo", "Sim", "testar_laudo deve ser S ou N"),
        (
            "quantidade_maxima_de_dias_de_licenca",
            "trinta",
            "deve ser inteiro",
        ),
        ("pesquisar_licencas_no_sigpec", "S", "incoerentes"),
    ],
)
def test_arquivo_invalido_nao_grava_nada(
    tmp_path, monkeypatch, campo, valor, mensagem
):
    linhas = _linhas_do_arquivo()
    linhas[0] = {**linhas[0], "codigo_cargo": "99001"}
    linhas[1] = {**linhas[1], "codigo_cargo": "99002", campo: valor}
    arquivo = tmp_path / "cargos.csv"
    _escrever_arquivo(arquivo, linhas[:2])
    monkeypatch.setattr(seed, "ARQUIVO", arquivo)

    with pytest.raises(ValueError, match=mensagem):
        seed.popular_cargos_base(django_apps, None)

    assert not CargoBase.objects.filter(
        codigo_cargo__in=["99001", "99002"]
    ).exists()


@pytest.mark.django_db
def test_arquivo_com_codigo_repetido_e_recusado(tmp_path, monkeypatch):
    linhas = _linhas_do_arquivo()[:2]
    linhas[1] = {**linhas[1], "codigo_cargo": linhas[0]["codigo_cargo"]}
    arquivo = tmp_path / "cargos.csv"
    _escrever_arquivo(arquivo, linhas)
    monkeypatch.setattr(seed, "ARQUIVO", arquivo)

    with pytest.raises(ValueError, match="código do cargo repetido"):
        seed.ler_cargos(CargoBase)


@pytest.mark.django_db
def test_descricao_acima_do_limite_e_recusada(tmp_path, monkeypatch):
    linhas = _linhas_do_arquivo()[:1]
    linhas[0] = {**linhas[0], "descricao_eol": "A" * 256}
    arquivo = tmp_path / "cargos.csv"
    _escrever_arquivo(arquivo, linhas)
    monkeypatch.setattr(seed, "ARQUIVO", arquivo)

    with pytest.raises(ValueError, match="mais de 255 caracteres"):
        seed.ler_cargos(CargoBase)
