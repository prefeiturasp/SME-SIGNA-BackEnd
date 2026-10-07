"""Testes para os serializadores de CargoBase."""

from datetime import date

import pytest
from rest_framework import serializers

from apps.gestao.__tests__.factories import criar_cargo_base
from apps.gestao.api.serializers.cargo_base_serializer import (
    MSG_DATA_FINAL_DO_PERIODO_OBRIGATORIO,
    MSG_LICENCA_OBRIGATORIO,
    MSG_LICENCA_ZERADA,
    MSG_PERIODO_FECHADO_OBRIGATORIO,
    MSG_QUANTIDADE_MAXIMA_DE_DIAS_OBRIGATORIO,
    CargoBaseReadSerializer,
    CargoBaseUpdateSerializer,
    CargoBaseWriteSerializer,
    validate_data_final_do_periodo,
    validate_quantidade_maxima_de_dias_de_licenca,
)
from apps.gestao.models.cargo_base import CargoBase


def test_validate_quantidade_maxima_de_dias_de_licenca_ignora_quantidade_sem_pesquisa():
    """Verifica que a quantidade não é exigida quando a pesquisa está desligada."""
    attrs = {"pesquisar_licencas_no_sigpec": False}

    resultado = validate_quantidade_maxima_de_dias_de_licenca(attrs)

    assert resultado == attrs


def test_validate_quantidade_maxima_de_dias_de_licenca_aceita_quantidade_positiva():
    """Verifica que a pesquisa aceita uma quantidade positiva."""
    attrs = {
        "pesquisar_licencas_no_sigpec": True,
        "quantidade_maxima_de_dias_de_licenca": 30,
    }

    resultado = validate_quantidade_maxima_de_dias_de_licenca(attrs)

    assert resultado == attrs


def test_validate_quantidade_maxima_de_dias_de_licenca_rejeita_quantidade_ausente():
    """Verifica que a pesquisa exige uma quantidade máxima de dias."""
    attrs = {"pesquisar_licencas_no_sigpec": True}

    with pytest.raises(serializers.ValidationError) as exc_info:
        validate_quantidade_maxima_de_dias_de_licenca(attrs)

    assert MSG_LICENCA_OBRIGATORIO in str(exc_info.value)


def test_validate_quantidade_maxima_de_dias_de_licenca_rejeita_quantidade_zero():
    """Verifica que a pesquisa rejeita quantidade máxima zerada."""
    attrs = {
        "pesquisar_licencas_no_sigpec": True,
        "quantidade_maxima_de_dias_de_licenca": 0,
    }

    with pytest.raises(serializers.ValidationError) as exc_info:
        validate_quantidade_maxima_de_dias_de_licenca(attrs)

    assert MSG_LICENCA_ZERADA in str(exc_info.value)


def test_validate_quantidade_maxima_de_dias_de_licenca_rejeita_quantidade_sem_pesquisa():
    """Verifica que a quantidade exige pesquisa de licenças ativa."""
    attrs = {"quantidade_maxima_de_dias_de_licenca": 30}

    with pytest.raises(serializers.ValidationError) as exc_info:
        validate_quantidade_maxima_de_dias_de_licenca(attrs)

    assert MSG_QUANTIDADE_MAXIMA_DE_DIAS_OBRIGATORIO in str(exc_info.value)


def test_validate_data_final_do_periodo_ignora_quando_periodo_nao_fechado():
    """Verifica que a data final não é exigida sem período fechado."""
    attrs = {"possui_periodo_fechado": False}

    resultado = validate_data_final_do_periodo(attrs)

    assert resultado == attrs


def test_validate_data_final_do_periodo_aceita_data_informada():
    """Verifica que a data final é aceita com período fechado ativo."""
    attrs = {
        "possui_periodo_fechado": True,
        "data_fim_periodo": date(2026, 12, 31),
    }

    resultado = validate_data_final_do_periodo(attrs)

    assert resultado == attrs


def test_validate_data_final_do_periodo_rejeita_data_ausente():
    """Verifica que a data final é obrigatória com período fechado ativo."""
    attrs = {"possui_periodo_fechado": True}

    with pytest.raises(serializers.ValidationError) as exc_info:
        validate_data_final_do_periodo(attrs)

    assert MSG_DATA_FINAL_DO_PERIODO_OBRIGATORIO in str(exc_info.value)


def test_validate_data_final_do_periodo_rejeita_periodo_fechado_ausente():
    """Verifica que o período fechado é obrigatório com data final informada."""
    attrs = {"data_fim_periodo": date(2026, 12, 31)}

    with pytest.raises(serializers.ValidationError) as exc_info:
        validate_data_final_do_periodo(attrs)

    assert MSG_PERIODO_FECHADO_OBRIGATORIO in str(exc_info.value)


def test_validate_data_final_do_periodo_rejeita_data_com_periodo_desligado():
    """Verifica que data final exige período fechado ativo."""
    attrs = {
        "possui_periodo_fechado": False,
        "data_fim_periodo": date(2026, 12, 31),
    }

    with pytest.raises(serializers.ValidationError) as exc_info:
        validate_data_final_do_periodo(attrs)

    assert MSG_PERIODO_FECHADO_OBRIGATORIO in str(exc_info.value)


@pytest.mark.django_db
def test_read_serializer_expoe_todos_os_campos():
    """Verifica que o serializer de leitura expõe os campos esperados."""
    cargo = criar_cargo_base()

    data = CargoBaseReadSerializer(cargo).data

    assert data["codigo_cargo"] == cargo.codigo_cargo
    assert data["descricao_completa"] == cargo.descricao_completa
    assert data["descricao_resumida"] == cargo.descricao_resumida
    assert data["grupamento"] == cargo.grupamento
    assert data["situacao_funcional"] == cargo.situacao_funcional
    assert data["status"] == cargo.status
    assert data["utilizado_para_funcoes"] == cargo.utilizado_para_funcoes
    assert (
        data["utilizado_para_designacoes"] == cargo.utilizado_para_designacoes
    )
    assert data["utilizado_para_ste"] == cargo.utilizado_para_ste
    assert data["utilizado_para_permutas"] == cargo.utilizado_para_permutas
    assert data["cargo_base_ficticio"] == cargo.cargo_base_ficticio
    assert data["testar_laudo"] == cargo.testar_laudo
    assert (
        data["pesquisar_licencas_no_sigpec"]
        == cargo.pesquisar_licencas_no_sigpec
    )
    assert (
        data["quantidade_maxima_de_dias_de_licenca"]
        == cargo.quantidade_maxima_de_dias_de_licenca
    )
    assert data["permite_substituicao"] == cargo.permite_substituicao
    assert data["possui_periodo_fechado"] == cargo.possui_periodo_fechado
    assert data["data_fim_periodo"] == cargo.data_fim_periodo
    assert "criado_em" in data


@pytest.mark.django_db
def test_read_serializer_expoe_displays_legiveis():
    """Verifica que o serializer de leitura expõe os labels legíveis."""
    cargo = criar_cargo_base(
        grupamento=CargoBase.Grupamento.GESTORES_EDUCACAO,
        situacao_funcional=CargoBase.SituacaoFuncional.EFETIVO,
        status=CargoBase.Status.ATIVO,
    )

    data = CargoBaseReadSerializer(cargo).data

    assert data["grupamento_display"] == "Gestores - educação"
    assert data["situacao_funcional_display"] == "Efetivo"
    assert data["status_display"] == "Ativo"


@pytest.mark.django_db
def test_write_serializer_valido_cria_cargo_base():
    """Verifica que o serializer de escrita valida e cria um cargo base."""
    payload = {
        "codigo_cargo": "9085",
        "descricao_completa": "ASSISTENTE DE DIRETOR DE ESCOLA",
        "descricao_resumida": "Assistente de Diretor",
        "grupamento": CargoBase.Grupamento.GESTORES_EDUCACAO,
        "situacao_funcional": CargoBase.SituacaoFuncional.EFETIVO,
    }

    serializer = CargoBaseWriteSerializer(data=payload)

    assert serializer.is_valid(), serializer.errors
    cargo = serializer.save()
    assert cargo.status == CargoBase.Status.ATIVO


@pytest.mark.django_db
def test_write_serializer_valido_cria_cargo_base_com_campos_opcionais():
    """Verifica que o serializer de escrita valida e cria um cargo base."""
    payload = {
        "codigo_cargo": "9085",
        "descricao_completa": "ASSISTENTE DE DIRETOR DE ESCOLA",
        "descricao_resumida": "Assistente de Diretor",
        "grupamento": CargoBase.Grupamento.GESTORES_EDUCACAO,
        "situacao_funcional": CargoBase.SituacaoFuncional.EFETIVO,
        "testar_laudo": True,
        "pesquisar_licencas_no_sigpec": True,
        "quantidade_maxima_de_dias_de_licenca": 30,
    }

    serializer = CargoBaseWriteSerializer(data=payload)

    assert serializer.is_valid(), serializer.errors
    cargo = serializer.save()
    assert cargo.pesquisar_licencas_no_sigpec
    assert cargo.quantidade_maxima_de_dias_de_licenca == 30
    assert cargo.testar_laudo


@pytest.mark.django_db
def test_write_serializer_rejeita_codigo_cargo_duplicado():
    """Verifica que o serializer rejeita código de cargo já cadastrado."""
    criar_cargo_base(codigo_cargo="9360")

    payload = {
        "codigo_cargo": "9360",
        "descricao_completa": "DIRETOR DE ESCOLA",
        "descricao_resumida": "Diretor",
        "grupamento": CargoBase.Grupamento.GESTORES_EDUCACAO,
        "situacao_funcional": CargoBase.SituacaoFuncional.EFETIVO,
    }

    serializer = CargoBaseWriteSerializer(data=payload)

    assert not serializer.is_valid()
    assert "codigo_cargo" in serializer.errors


@pytest.mark.django_db
def test_write_serializer_rejeita_quantidade_maxima_de_dias_de_licenca_invalida():
    """Verifica que campos vindos do EOL não são editáveis via atualização."""
    payload = {
        "codigo_cargo": "10000",
        "descricao_completa": "CARGO QUALQUER",
        "descricao_resumida": "Cargo Qualquer",
        "grupamento": CargoBase.Grupamento.GESTORES_EDUCACAO,
        "situacao_funcional": CargoBase.SituacaoFuncional.EFETIVO,
        "pesquisar_licencas_no_sigpec": True,
    }

    serializer = CargoBaseWriteSerializer(data=payload)

    assert not serializer.is_valid()
    assert "quantidade_maxima_de_dias_de_licenca" in serializer.errors


@pytest.mark.django_db
def test_write_serializer_rejeita_quantidade_maxima_de_dias_de_licenca_zero():
    """Verifica que campos vindos do EOL não são editáveis via atualização."""
    payload = {
        "codigo_cargo": "10000",
        "descricao_completa": "CARGO QUALQUER",
        "descricao_resumida": "Cargo Qualquer",
        "grupamento": CargoBase.Grupamento.GESTORES_EDUCACAO,
        "situacao_funcional": CargoBase.SituacaoFuncional.EFETIVO,
        "pesquisar_licencas_no_sigpec": True,
        "quantidade_maxima_de_dias_de_licenca": 0,
    }

    serializer = CargoBaseWriteSerializer(data=payload)

    assert not serializer.is_valid()
    assert "quantidade_maxima_de_dias_de_licenca" in serializer.errors


@pytest.mark.django_db
def test_write_serializer_rejeita_grupamento_invalido():
    """Verifica que o serializer rejeita valores fora das choices."""
    payload = {
        "codigo_cargo": "9999",
        "descricao_completa": "CARGO QUALQUER",
        "descricao_resumida": "Cargo Qualquer",
        "grupamento": "INVALIDO",
        "situacao_funcional": CargoBase.SituacaoFuncional.EFETIVO,
    }

    serializer = CargoBaseWriteSerializer(data=payload)

    assert not serializer.is_valid()
    assert "grupamento" in serializer.errors


@pytest.mark.django_db
def test_update_serializer_altera_campos_editaveis():
    """Verifica que o serializer de atualização altera os campos permitidos."""
    cargo = criar_cargo_base(
        descricao_resumida="Diretor de Escola",
        utilizado_para_permutas=False,
    )

    payload = {
        "descricao_resumida": "Diretor de Escola Municipal",
        "utilizado_para_permutas": True,
    }

    serializer = CargoBaseUpdateSerializer(cargo, data=payload, partial=True)

    assert serializer.is_valid(), serializer.errors
    cargo_atualizado = serializer.save()
    assert cargo_atualizado.descricao_resumida == "Diretor de Escola Municipal"
    assert cargo_atualizado.utilizado_para_permutas is True


@pytest.mark.django_db
def test_update_serializer_nao_expoe_codigo_cargo_e_descricao_completa():
    """Verifica que campos vindos do EOL não são editáveis via atualização."""
    cargo = criar_cargo_base(
        codigo_cargo="9360", descricao_completa="DIRETOR DE ESCOLA MUNICIPAL"
    )

    payload = {
        "codigo_cargo": "9999",
        "descricao_completa": "OUTRO CARGO QUALQUER",
    }

    serializer = CargoBaseUpdateSerializer(cargo, data=payload, partial=True)

    assert serializer.is_valid(), serializer.errors
    cargo_atualizado = serializer.save()
    assert cargo_atualizado.codigo_cargo == "9360"
    assert cargo_atualizado.descricao_completa == "DIRETOR DE ESCOLA MUNICIPAL"


@pytest.mark.django_db
def test_update_serializer_rejeita_quantidade_maxima_de_dias_de_licenca_invalida():
    """Verifica que campos vindos do EOL não são editáveis via atualização."""
    cargo = criar_cargo_base(
        codigo_cargo="9360", descricao_completa="DIRETOR DE ESCOLA MUNICIPAL"
    )

    payload = {"pesquisar_licencas_no_sigpec": True}

    serializer = CargoBaseUpdateSerializer(cargo, data=payload, partial=True)

    assert not serializer.is_valid()
    assert "quantidade_maxima_de_dias_de_licenca" in serializer.errors


@pytest.mark.django_db
def test_update_serializer_rejeita_data_fim_periodo_ausente():
    """Verifica que a data final é obrigatória com período fechado ativo."""
    cargo = criar_cargo_base(codigo_cargo="3362")

    payload = {"possui_periodo_fechado": True}

    serializer = CargoBaseUpdateSerializer(cargo, data=payload, partial=True)

    assert not serializer.is_valid()
    assert "data_fim_periodo" in serializer.errors
    assert (
        MSG_DATA_FINAL_DO_PERIODO_OBRIGATORIO
        in serializer.errors["data_fim_periodo"][0]
    )


@pytest.mark.django_db
def test_update_serializer_altera_periodo_fechado_com_data_final():
    """Verifica que o serializer aceita período fechado com data final."""
    cargo = criar_cargo_base(codigo_cargo="3363")

    payload = {
        "possui_periodo_fechado": True,
        "data_fim_periodo": "2026-12-31",
    }

    serializer = CargoBaseUpdateSerializer(cargo, data=payload, partial=True)

    assert serializer.is_valid(), serializer.errors
    cargo_atualizado = serializer.save()
    assert cargo_atualizado.possui_periodo_fechado is True
    assert cargo_atualizado.data_fim_periodo == date(2026, 12, 31)


@pytest.mark.django_db
def test_update_serializer_rejeita_quantidade_maxima_de_dias_de_licenca_zero():
    """Verifica que campos vindos do EOL não são editáveis via atualização."""
    cargo = criar_cargo_base(
        codigo_cargo="3361", descricao_completa="DIRETOR DE ESCOLA MUNICIPAL"
    )

    payload = {
        "pesquisar_licencas_no_sigpec": True,
        "quantidade_maxima_de_dias_de_licenca": 0,
    }

    serializer = CargoBaseUpdateSerializer(cargo, data=payload, partial=True)
    resposta_esperada = (
        "Quantidade máxima de dias de licença deve ser maior que zero"
    )

    assert not serializer.is_valid()
    assert "quantidade_maxima_de_dias_de_licenca" in serializer.errors
    assert (
        resposta_esperada
        in serializer.errors["quantidade_maxima_de_dias_de_licenca"][0]
    )


@pytest.mark.django_db
def test_update_serializer_rejeita_quantidade_de_licenca_sem_pesquisa_ativa():
    """Verifica que a atualização usa a pesquisa da instância na validação."""
    cargo = criar_cargo_base(codigo_cargo="3364")

    serializer = CargoBaseUpdateSerializer(
        cargo,
        data={"quantidade_maxima_de_dias_de_licenca": 30},
        partial=True,
    )

    assert not serializer.is_valid()
    assert "quantidade_maxima_de_dias_de_licenca" in serializer.errors
    assert (
        MSG_QUANTIDADE_MAXIMA_DE_DIAS_OBRIGATORIO
        in serializer.errors["quantidade_maxima_de_dias_de_licenca"][0]
    )
