"""Testes para serviço de cessação."""

import datetime

import pytest
from rest_framework.exceptions import ValidationError

from apps.designacao.__tests__.factories import (
    criar_ato_cessacao,
    criar_ato_designacao,
    criar_ato_insubsistencia,
)
from apps.designacao.models.ato_administrativo import AtoAdministrativo
from apps.designacao.services.cessacao_service import CessacaoService


@pytest.mark.django_db
class TestCessacaoService:
    """Testes para cessacao service."""

    def _data(self, ato_pai, **kwargs):
        """Método auxiliar para payload de criação."""
        base = {
            "ato_pai": ato_pai,
            "numero_portaria": 12345,
            "ano_vigente": "2024",
            "sei_numero": "SEI-999999",
            "data_cessacao": "2024-03-10",
        }
        base.update(kwargs)
        return base

    def test_erro_ato_pai_insubsistente(self):
        """Verifica erro ao criar cessação para designação insubsistente."""
        designacao = criar_ato_designacao()
        criar_ato_insubsistencia(designacao)
        designacao.ativo = False
        designacao.save(update_fields=["ativo"])

        with pytest.raises(ValidationError, match="insubsistente"):
            CessacaoService.criar(self._data(designacao))

    def test_atualizar_campos_do_ato(self):
        """Verifica atualização de campos pertencentes ao ato."""
        designacao = criar_ato_designacao()
        cessacao = criar_ato_cessacao(designacao, numero_portaria="111")

        atualizado = CessacaoService.atualizar(
            cessacao,
            {"ato_pai": designacao, "numero_portaria": "999"},
        )

        atualizado.refresh_from_db()
        assert atualizado.numero_portaria == "999"

    def test_atualizar_campos_do_detalhe(self):
        """Verifica atualização de campos pertencentes ao detalhe."""
        designacao = criar_ato_designacao()
        cessacao = criar_ato_cessacao(
            designacao, data_cessacao=datetime.date(2024, 3, 1)
        )

        atualizado = CessacaoService.atualizar(
            cessacao,
            {
                "ato_pai": designacao,
                "data_cessacao": datetime.date(2024, 6, 15),
                "a_pedido": True,
            },
        )

        atualizado.cessacao_detalhe.refresh_from_db()
        assert atualizado.cessacao_detalhe.data_cessacao == datetime.date(
            2024, 6, 15
        )
        assert atualizado.cessacao_detalhe.a_pedido is True

    def test_atualizar_campos_do_ato_e_do_detalhe(self):
        """Verifica atualização simultânea de campos do ato e do detalhe."""
        designacao = criar_ato_designacao()
        cessacao = criar_ato_cessacao(
            designacao,
            numero_portaria="111",
            data_cessacao=datetime.date(2024, 3, 1),
        )

        atualizado = CessacaoService.atualizar(
            cessacao,
            {
                "ato_pai": designacao,
                "numero_portaria": "222",
                "data_cessacao": datetime.date(2024, 7, 1),
            },
        )

        atualizado.refresh_from_db()
        atualizado.cessacao_detalhe.refresh_from_db()
        assert atualizado.numero_portaria == "222"
        assert atualizado.cessacao_detalhe.data_cessacao == datetime.date(
            2024, 7, 1
        )

    def test_erro_atualizar_ato_pai_insubsistente(self):
        """Verifica erro ao atualizar cessação com designação insubsistente."""
        designacao = criar_ato_designacao()
        cessacao = criar_ato_cessacao(designacao)
        criar_ato_insubsistencia(designacao)
        designacao.ativo = False
        designacao.save(update_fields=["ativo"])

        with pytest.raises(ValidationError, match="insubsistente"):
            CessacaoService.atualizar(
                cessacao,
                {"ato_pai": designacao, "numero_portaria": "999"},
            )

    def test_erro_atualizar_quando_ja_publicado(self):
        """Verifica que cessação publicada não pode ser atualizada."""
        designacao = criar_ato_designacao()
        cessacao = criar_ato_cessacao(designacao)
        cessacao.status_publicacao = (
            AtoAdministrativo.StatusPublicacao.PUBLICADO
        )
        cessacao.save(update_fields=["status_publicacao"])

        with pytest.raises(ValidationError, match="publicada"):
            CessacaoService.atualizar(
                cessacao,
                {"ato_pai": designacao, "numero_portaria": "999"},
            )
