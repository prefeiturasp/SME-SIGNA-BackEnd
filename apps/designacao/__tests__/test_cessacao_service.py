"""Testes para serviço de cessação."""

import pytest
from rest_framework.exceptions import ValidationError

from apps.designacao.__tests__.factories import (
    criar_ato_designacao,
    criar_ato_insubsistencia,
)
from apps.designacao.services.cessacao_service import CessacaoService


@pytest.mark.django_db
class TestCessacaoService:
    """Testes para cessacao service."""

    def _data(self, ato_pai, **kwargs):
        """Método auxiliar para payload de criação."""
        base = {
            "ato_pai": ato_pai,
            "numero_portaria": "12345",
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
