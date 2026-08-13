"""Testes para utilitários de serialização."""

import pytest
from rest_framework import serializers

from apps.designacao.api.serializers.utils import (
    NullableDateField,
    extrair_mensagem_erro,
    validar_somente_numeros,
)


class TestNullableDateField:
    """Testes para NullableDateField."""

    def test_string_vazia_retorna_none(self):
        """Verifica que string vazia é tratada como valor nulo."""
        field = NullableDateField()
        is_empty, value = field.validate_empty_values("")
        assert is_empty is True
        assert value is None

    def test_data_valida_delega_para_classe_base(self):
        """Verifica que valores não vazios seguem a validação padrão."""
        field = NullableDateField()
        is_empty, value = field.validate_empty_values("2024-01-01")
        assert is_empty is False
        assert value == "2024-01-01"


class TestValidarSomenteNumeros:
    """Testes para validar_somente_numeros."""

    def test_valor_apenas_numeros_e_valido(self):
        """Verifica que string apenas com dígitos é retornada."""
        assert validar_somente_numeros("12345") == "12345"

    def test_valor_com_letras_gera_erro(self):
        """Verifica que caracteres não numéricos disparam erro."""
        with pytest.raises(serializers.ValidationError):
            validar_somente_numeros("12A45")


class TestExtrairMensagemErro:
    """Testes para extrair_mensagem_erro."""

    def test_extrai_de_string(self):
        """Verifica extração direta de uma string."""
        assert extrair_mensagem_erro("erro simples") == "erro simples"

    def test_extrai_de_lista(self):
        """Verifica extração do primeiro item de uma lista."""
        assert extrair_mensagem_erro(["erro 1", "erro 2"]) == "erro 1"

    def test_extrai_de_dict(self):
        """Verifica extração do primeiro valor de um dicionário."""
        detail = {"campo": "erro do campo"}
        assert extrair_mensagem_erro(detail) == "erro do campo"

    def test_extrai_de_dict_aninhado_em_lista(self):
        """Verifica extração recursiva de dict contendo lista."""
        detail = {"campo": ["erro aninhado"]}
        assert extrair_mensagem_erro(detail) == "erro aninhado"

    def test_extrai_de_lista_vazia_retorna_str(self):
        """Verifica que lista vazia cai no caso base e vira string."""
        assert extrair_mensagem_erro([]) == "[]"
