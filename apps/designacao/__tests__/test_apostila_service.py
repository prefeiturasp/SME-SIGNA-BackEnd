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

    def test_erro_alteracao_em_campo_inexistente(self):
        """Verifica erro ao alterar campo inexistente no ato pai/detalhe."""
        d = criar_ato_designacao()
        with pytest.raises(ValidationError, match="não encontrado"):
            ApostilaService.criar(
                self._data(
                    d,
                    alteracoes=[
                        {
                            "campo_alterado": "campo_inexistente",
                            "valor_novo": "x",
                        },
                    ],
                )
            )

    def test_erro_alteracao_em_campo_protegido(self):
        """Verifica erro ao alterar campo protegido via apostila."""
        d = criar_ato_designacao()
        with pytest.raises(ValidationError, match="não pode ser alterado"):
            ApostilaService.criar(
                self._data(
                    d,
                    alteracoes=[
                        {"campo_alterado": "tipo", "valor_novo": "CESSACAO"},
                    ],
                )
            )

    def test_get_detalhe_retorna_none_para_tipo_sem_detalhe(self):
        """Verifica que _get_detalhe retorna None para tipos sem detalhe."""
        d = criar_ato_designacao()
        apostila = criar_ato_apostila(d)

        assert ApostilaService._get_detalhe(apostila) is None

    # ── Cenário 4: alterações que cruzam para a designação de origem ─────────

    def test_criar_com_alteracao_na_designacao_de_origem_de_uma_cessacao(self):
        """Verifica que uma apostila de cessação pode alterar a designação."""
        d = criar_ato_designacao(unidade_proponente="Escola Antiga")
        c = criar_ato_cessacao(d)

        ApostilaService.criar(
            self._data(
                c,
                alteracoes=[
                    {
                        "campo_alterado": "unidade_proponente",
                        "valor_novo": "Escola Nova",
                        "tipo_ato_alvo": "DESIGNACAO",
                    },
                ],
            )
        )

        d.designacao_detalhe.refresh_from_db()
        assert d.designacao_detalhe.unidade_proponente == "Escola Nova"

    def test_permite_alterar_mesmo_nome_de_campo_na_cessacao_e_na_designacao(
        self,
    ):
        """Verifica que o mesmo nome de campo não colide entre alvos."""
        d = criar_ato_designacao(numero_portaria="001")
        c = criar_ato_cessacao(d, numero_portaria="050")

        ApostilaService.criar(
            self._data(
                c,
                alteracoes=[
                    {
                        "campo_alterado": "numero_portaria",
                        "valor_novo": "051",
                    },
                    {
                        "campo_alterado": "numero_portaria",
                        "valor_novo": "002",
                        "tipo_ato_alvo": "DESIGNACAO",
                    },
                ],
            )
        )

        c.refresh_from_db()
        d.refresh_from_db()
        assert c.numero_portaria == "051"
        assert d.numero_portaria == "002"

    def test_registra_ato_alterado_em_cada_alteracao(self):
        """Verifica que cada alteração grava o ato que foi de fato afetado."""
        d = criar_ato_designacao(unidade_proponente="Escola Antiga")
        c = criar_ato_cessacao(d, numero_portaria="050")

        ato = ApostilaService.criar(
            self._data(
                c,
                alteracoes=[
                    {
                        "campo_alterado": "numero_portaria",
                        "valor_novo": "051",
                    },
                    {
                        "campo_alterado": "unidade_proponente",
                        "valor_novo": "Escola Nova",
                        "tipo_ato_alvo": "DESIGNACAO",
                    },
                ],
            )
        )

        alteracoes = {
            alt.campo_alterado: alt.ato_alterado_id
            for alt in ato.apostila_detalhe.alteracoes.all()
        }
        assert alteracoes["numero_portaria"] == c.pk
        assert alteracoes["unidade_proponente"] == d.pk

    def test_alvo_designacao_explicito_e_redundante_mas_valido_no_ato_pai(
        self,
    ):
        """Verifica que DESIGNACAO como alvo redundante resolve pro ato_pai."""
        d = criar_ato_designacao(numero_portaria="001")
        ApostilaService.criar(
            self._data(
                d,
                alteracoes=[
                    {
                        "campo_alterado": "numero_portaria",
                        "valor_novo": "999",
                        "tipo_ato_alvo": "DESIGNACAO",
                    },
                ],
            )
        )
        d.refresh_from_db()
        assert d.numero_portaria == "999"

    def test_erro_tipo_ato_alvo_cessacao_quando_ato_pai_e_designacao(self):
        """Verifica erro ao pedir CESSACAO como alvo a partir de uma designação."""
        d = criar_ato_designacao()
        with pytest.raises(ValidationError, match="Não é possível alterar"):
            ApostilaService.criar(
                self._data(
                    d,
                    alteracoes=[
                        {
                            "campo_alterado": "numero_portaria",
                            "valor_novo": "999",
                            "tipo_ato_alvo": "CESSACAO",
                        },
                    ],
                )
            )

    def test_erro_tipo_ato_alvo_apostila_nao_suportado(self):
        """Verifica erro ao pedir um alvo fora da cadeia ato_pai/designação."""
        d = criar_ato_designacao()
        c = criar_ato_cessacao(d)
        with pytest.raises(ValidationError, match="Não é possível alterar"):
            ApostilaService.criar(
                self._data(
                    c,
                    alteracoes=[
                        {
                            "campo_alterado": "numero_portaria",
                            "valor_novo": "999",
                            "tipo_ato_alvo": "APOSTILA",
                        },
                    ],
                )
            )

    # ── Cenário 5: texto da portaria fica congelado após publicação ──────────

    def test_erro_ao_alterar_texto_sei_de_ato_ja_publicado(self):
        """Verifica que não é possível reescrever texto_sei já publicado."""
        d = criar_ato_designacao(doc=datetime.date(2024, 5, 1))
        with pytest.raises(ValidationError, match="já publicado"):
            ApostilaService.criar(
                self._data(
                    d,
                    alteracoes=[
                        {
                            "campo_alterado": "texto_sei",
                            "valor_novo": "Novo texto",
                        },
                    ],
                )
            )

    def test_permite_alterar_texto_sei_quando_ato_nao_publicado(self):
        """Verifica que texto_sei pode ser corrigido antes da publicação."""
        d = criar_ato_designacao()
        assert d.doc is None
        ApostilaService.criar(
            self._data(
                d,
                alteracoes=[
                    {"campo_alterado": "texto_sei", "valor_novo": "Corrigido"},
                ],
            )
        )
        d.refresh_from_db()
        assert d.texto_sei == "Corrigido"

    def test_erro_ao_alterar_texto_sei_da_designacao_ja_publicada_via_cessacao(
        self,
    ):
        """Verifica o congelamento também quando o alvo é a designação."""
        d = criar_ato_designacao(doc=datetime.date(2024, 5, 1))
        c = criar_ato_cessacao(d)
        with pytest.raises(ValidationError, match="já publicado"):
            ApostilaService.criar(
                self._data(
                    c,
                    alteracoes=[
                        {
                            "campo_alterado": "texto_sei",
                            "valor_novo": "Novo texto",
                            "tipo_ato_alvo": "DESIGNACAO",
                        },
                    ],
                )
            )
