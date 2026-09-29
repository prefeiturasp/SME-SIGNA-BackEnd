"""Testes para o TextoSeiService."""

import pytest
from rest_framework.exceptions import ValidationError

from apps.designacao.models.ato_administrativo import AtoAdministrativo
from apps.designacao.services.texto_sei_service import TextoSeiService
from apps.gestao.__tests__.factories import criar_modelo_portaria
from apps.gestao.models.modelo_portaria import ModeloPortaria


@pytest.mark.django_db
def test_gerar_preview_substitui_variaveis_do_modelo():
    """Verifica que o texto final tem as variáveis substituídas."""
    modelo = criar_modelo_portaria(
        tipo_portaria=AtoAdministrativo.Tipo.DESIGNACAO,
        texto_portaria=(
            "Designa [[NOME_SERVIDOR]], RF [[NUMERO_RF]], para [[CARGO]]."
        ),
    )

    modelo_usado, texto = TextoSeiService.gerar_preview(
        tipo_portaria=AtoAdministrativo.Tipo.DESIGNACAO,
        tipo_ato_pai="",
        tipo_cargo=ModeloPortaria.TipoCargo.CARGO_VAGO,
        dados={
            "NOME_SERVIDOR": "Maria Antônia Herrera",
            "NUMERO_RF": "1234567",
            "CARGO": "Coordenador Pedagógico",
        },
    )

    assert modelo_usado == modelo
    assert texto == (
        "Designa Maria Antônia Herrera, RF 1234567, "
        "para Coordenador Pedagógico."
    )


@pytest.mark.django_db
def test_gerar_preview_substitui_placeholder_sem_dado_por_vazio():
    """Verifica que uma variável sem valor correspondente vira string vazia."""
    criar_modelo_portaria(
        tipo_portaria=AtoAdministrativo.Tipo.DESIGNACAO,
        texto_portaria="Cargo: [[CARGO]].",
    )

    _, texto = TextoSeiService.gerar_preview(
        tipo_portaria=AtoAdministrativo.Tipo.DESIGNACAO,
        tipo_ato_pai="",
        tipo_cargo=ModeloPortaria.TipoCargo.CARGO_VAGO,
        dados={},
    )

    assert texto == "Cargo: ."


@pytest.mark.django_db
def test_gerar_preview_resolve_modelo_por_tipo_ato_pai():
    """Verifica que apostilas de designação e de cessação usam modelos distintos."""  # noqa: E501
    criar_modelo_portaria(
        tipo_portaria=AtoAdministrativo.Tipo.APOSTILA,
        tipo_ato_pai=AtoAdministrativo.Tipo.DESIGNACAO,
        texto_portaria="Apostila de designação.",
    )
    criar_modelo_portaria(
        tipo_portaria=AtoAdministrativo.Tipo.APOSTILA,
        tipo_ato_pai=AtoAdministrativo.Tipo.CESSACAO,
        texto_portaria="Apostila de cessação.",
    )

    _, texto = TextoSeiService.gerar_preview(
        tipo_portaria=AtoAdministrativo.Tipo.APOSTILA,
        tipo_ato_pai=AtoAdministrativo.Tipo.CESSACAO,
        tipo_cargo=ModeloPortaria.TipoCargo.CARGO_VAGO,
        dados={},
    )

    assert texto == "Apostila de cessação."


@pytest.mark.django_db
def test_gerar_preview_resolve_modelo_por_tipo_cargo():
    """Verifica que designação de cargo vago e disponível usam modelos distintos."""  # noqa: E501
    criar_modelo_portaria(
        tipo_portaria=AtoAdministrativo.Tipo.DESIGNACAO,
        tipo_cargo=ModeloPortaria.TipoCargo.CARGO_VAGO,
        texto_portaria="Designação para cargo vago.",
    )
    criar_modelo_portaria(
        tipo_portaria=AtoAdministrativo.Tipo.DESIGNACAO,
        tipo_cargo=ModeloPortaria.TipoCargo.CARGO_DISPONIVEL,
        texto_portaria="Designação para cargo disponível.",
    )

    _, texto = TextoSeiService.gerar_preview(
        tipo_portaria=AtoAdministrativo.Tipo.DESIGNACAO,
        tipo_ato_pai="",
        tipo_cargo=ModeloPortaria.TipoCargo.CARGO_DISPONIVEL,
        dados={},
    )

    assert texto == "Designação para cargo disponível."


@pytest.mark.django_db
def test_gerar_preview_levanta_erro_sem_modelo_ativo():
    """Verifica que a ausência de modelo ativo gera erro de validação."""
    with pytest.raises(ValidationError):
        TextoSeiService.gerar_preview(
            tipo_portaria=AtoAdministrativo.Tipo.CESSACAO,
            tipo_ato_pai="",
            tipo_cargo=ModeloPortaria.TipoCargo.CARGO_VAGO,
            dados={},
        )


@pytest.mark.django_db
def test_gerar_preview_levanta_erro_quando_tipo_cargo_nao_bate():
    """Verifica que um modelo cadastrado para outro tipo_cargo não é usado."""
    criar_modelo_portaria(
        tipo_portaria=AtoAdministrativo.Tipo.DESIGNACAO,
        tipo_cargo=ModeloPortaria.TipoCargo.CARGO_VAGO,
    )

    with pytest.raises(ValidationError):
        TextoSeiService.gerar_preview(
            tipo_portaria=AtoAdministrativo.Tipo.DESIGNACAO,
            tipo_ato_pai="",
            tipo_cargo=ModeloPortaria.TipoCargo.CARGO_DISPONIVEL,
            dados={},
        )


@pytest.mark.django_db
def test_gerar_preview_ignora_modelo_inativo():
    """Verifica que um modelo inativo não é usado na geração do texto."""
    criar_modelo_portaria(
        tipo_portaria=AtoAdministrativo.Tipo.DESIGNACAO,
        status=ModeloPortaria.Status.INATIVO,
    )

    with pytest.raises(ValidationError):
        TextoSeiService.gerar_preview(
            tipo_portaria=AtoAdministrativo.Tipo.DESIGNACAO,
            tipo_ato_pai="",
            tipo_cargo=ModeloPortaria.TipoCargo.CARGO_VAGO,
            dados={},
        )
