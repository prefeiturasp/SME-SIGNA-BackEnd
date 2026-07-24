"""Testes para serviço de apostila."""

import datetime

import pytest
from rest_framework.exceptions import ValidationError

from apps.designacao.__tests__.factories import (
    criar_ato_apostila,
    criar_ato_cessacao,
    criar_ato_designacao,
    criar_ato_insubsistencia,
)
from apps.designacao.models.ato_administrativo import AtoAdministrativo
from apps.designacao.services.apostila_service import ApostilaService


@pytest.mark.django_db
class TestApostilaService:
    """Testes para apostila service."""

    def _data(self, ato_pai, **kwargs):
        """Método auxiliar para data."""
        base = {
            "ato_pai": ato_pai,
            "sei_numero": "12345",
            "observacao": "Obs",
            "alteracoes": [],
        }
        base.update(kwargs)
        return base

    # ── Criação básica ────────────────────────────────────────────────────────

    def test_criar_apostila_designacao_sucesso(self):
        """Verifica criar apostila designacao sucesso."""
        d = criar_ato_designacao()
        ato = ApostilaService.criar(self._data(d))
        assert ato.pk is not None
        assert ato.ato_pai_id == d.pk
        assert (
            ato.status_publicacao
            == AtoAdministrativo.StatusPublicacao.NAO_PUBLICADO
        )

    def test_criar_apostila_cessacao_sucesso(self):
        """Verifica criar apostila cessacao sucesso."""
        d = criar_ato_designacao()
        c = criar_ato_cessacao(d)
        ato = ApostilaService.criar(self._data(c))
        assert ato.pk is not None
        assert ato.ato_pai_id == c.pk

    # ── Cenário 2: validação de apostila existente ─────────────────────────────

    def test_erro_ao_criar_apostila_quando_ja_existe_apostila_valida(self):
        """Verifica erro ao criar apostila quando já existe apostila válida."""
        d = criar_ato_designacao()
        criar_ato_apostila(d)
        data = self._data(d)
        with pytest.raises(ValidationError, match="já foi apostilado"):
            ApostilaService.criar(data)

    def test_permite_criar_apostila_apos_insubsistencia_da_anterior(self):
        """Verifica permite criar apostila apos insubsistencia da anterior."""
        d = criar_ato_designacao()
        ap = criar_ato_apostila(d)
        criar_ato_insubsistencia(ap)
        ap.ativo = False
        ap.save(update_fields=["ativo"])
        ato = ApostilaService.criar(self._data(d))
        assert ato.pk is not None

    # ── Cenário 3: validações de estado da designação ─────────────────────────

    def test_erro_designacao_cessada(self):
        """Verifica erro designacao cessada."""
        d = criar_ato_designacao()
        criar_ato_cessacao(d)
        with pytest.raises(ValidationError, match="cessada"):
            ApostilaService.criar(self._data(d))

    def test_erro_designacao_prazo_finalizado(self):
        """Verifica erro designacao prazo finalizado."""
        ontem = datetime.date.today() - datetime.timedelta(days=1)
        d = criar_ato_designacao()
        d.designacao_detalhe.data_fim = ontem
        d.designacao_detalhe.save(update_fields=["data_fim"])
        with pytest.raises(ValidationError, match="prazo finalizado"):
            ApostilaService.criar(self._data(d))

    def test_permite_apostila_designacao_com_data_fim_futura(self):
        """Verifica permite apostila designacao com data fim futura."""
        amanha = datetime.date.today() + datetime.timedelta(days=1)
        d = criar_ato_designacao()
        d.designacao_detalhe.data_fim = amanha
        d.designacao_detalhe.save(update_fields=["data_fim"])
        ato = ApostilaService.criar(self._data(d))
        assert ato.pk is not None

    def test_permite_apostila_cessacao_mesmo_com_data_fim(self):
        # Validação de data_fim não se aplica a cessações
        """Verifica permite apostila cessacao mesmo com data fim."""
        ontem = datetime.date.today() - datetime.timedelta(days=1)
        d = criar_ato_designacao()
        d.designacao_detalhe.data_fim = ontem
        d.designacao_detalhe.save(update_fields=["data_fim"])
        c = criar_ato_cessacao(d)
        ato = ApostilaService.criar(self._data(c))
        assert ato.pk is not None

    def test_erro_ato_pai_insubsistente(self):
        """Verifica erro ato pai insubsistente."""
        d = criar_ato_designacao()
        criar_ato_insubsistencia(d)
        d.ativo = False
        d.save(update_fields=["ativo"])
        with pytest.raises(ValidationError, match="insubsistente"):
            ApostilaService.criar(self._data(d))

    # ── Cenário 1: edição de campos via alterações ────────────────────────────

    def test_criar_com_alteracao_em_campo_do_ato(self):
        """Verifica criar com alteracao em campo do ato."""
        d = criar_ato_designacao(numero_portaria="001")
        ApostilaService.criar(
            self._data(
                d,
                alteracoes=[
                    {"campo_alterado": "numero_portaria", "valor_novo": "999"},
                ],
            )
        )
        d.refresh_from_db()
        assert d.numero_portaria == "999"

    def test_criar_com_alteracao_em_campo_do_detalhe(self):
        """Verifica criar com alteracao em campo do detalhe."""
        d = criar_ato_designacao()
        ApostilaService.criar(
            self._data(
                d,
                alteracoes=[
                    {
                        "campo_alterado": "unidade_proponente",
                        "valor_novo": "Nova Escola",
                    },
                ],
            )
        )
        d.designacao_detalhe.refresh_from_db()
        assert d.designacao_detalhe.unidade_proponente == "Nova Escola"

    def test_criar_com_alteracao_tipo_vaga(self):
        """Verifica criar com alteracao tipo vaga."""
        d = criar_ato_designacao()
        ApostilaService.criar(
            self._data(
                d,
                alteracoes=[
                    {
                        "campo_alterado": "tipo_vaga",
                        "valor_novo": "DISPONIVEL",
                    },
                ],
            )
        )
        d.designacao_detalhe.refresh_from_db()
        assert d.designacao_detalhe.tipo_vaga == "DISPONIVEL"
