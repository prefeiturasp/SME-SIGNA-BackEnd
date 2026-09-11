"""Testes para o exception handler customizado da API."""

from rest_framework.exceptions import ValidationError

from apps.helpers.exception_handler import _flatten_errors, exception_handler


class TestFlattenErrors:
    """Testes para _flatten_errors."""

    def test_string_simples(self):
        """String sem prefixo é retornada como mensagem única."""
        assert _flatten_errors("erro simples") == ["erro simples"]

    def test_dict_simples(self):
        """Erro por campo é formatado como 'campo: mensagem'."""
        assert _flatten_errors({"nome": ["obrigatório"]}) == [
            "nome: obrigatório"
        ]

    def test_dict_aninhado(self):
        """Prefixo acumula os campos aninhados separados por ponto."""
        errors = {"servidor": {"nome": ["obrigatório"]}}
        assert _flatten_errors(errors) == ["servidor.nome: obrigatório"]

    def test_lista_de_erros(self):
        """Lista de erros não relacionados a campo mantém o prefixo vazio."""
        assert _flatten_errors(["erro 1", "erro 2"]) == ["erro 1", "erro 2"]


class TestExceptionHandler:
    """Testes para exception_handler."""

    def test_excecao_nao_tratada_pela_drf_retorna_none(self):
        """Quando a DRF não sabe tratar a exceção, o handler propaga None."""
        assert exception_handler(ValueError("erro inesperado"), {}) is None

    def test_response_dict_sem_detail_recebe_resumo(self):
        """Erros por campo (dict) ganham chave detail com o resumo."""
        exc = ValidationError(
            {"numero_portaria": ["Este campo é obrigatório."]}
        )

        response = exception_handler(exc, {})

        assert "detail" in response.data
        assert (
            response.data["detail"]
            == "numero_portaria: Este campo é obrigatório."
        )

    def test_response_dict_com_detail_nao_e_alterado(self):
        """Se o corpo já possui detail, o handler não sobrescreve o corpo."""
        exc = ValidationError(detail={"detail": "erro já descrito"})

        response = exception_handler(exc, {})

        assert response.data == {"detail": "erro já descrito"}

    def test_response_lista_e_convertido_para_dict_com_detail_e_errors(self):
        """Corpo de erro não-dict (lista) é envolvido em detail/errors."""
        exc = ValidationError(["erro geral", "outro erro"])

        response = exception_handler(exc, {})

        assert response.data["detail"] == "erro geral; outro erro"
        assert response.data["errors"] == ["erro geral", "outro erro"]
