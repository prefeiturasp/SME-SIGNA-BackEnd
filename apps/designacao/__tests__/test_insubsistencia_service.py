"""Testes para serviço de insubsistência."""

from unittest.mock import MagicMock

import pytest
from django.db.models import FloatField
from rest_framework.exceptions import ValidationError

from apps.designacao.__tests__.factories import (
    criar_ato_apostila,
    criar_ato_cessacao,
    criar_ato_designacao,
    criar_ato_insubsistencia,
)
from apps.designacao.models.ato_administrativo import AtoAdministrativo
from apps.designacao.services.insubsistencia_service import (
    InsubsistenciaService,
)


def _data(ato_pai, **kwargs):
    """Método auxiliar para data."""
    base = {
        "ato_pai": ato_pai,
        "numero_portaria": "111",
        "ano_vigente": "2024",
        "sei_numero": "SEI-I",
        "observacoes": "",
    }
    base.update(kwargs)
    return base


@pytest.mark.django_db
class TestInsubsistenciaService:
    """Testes para insubsistencia service."""

    def test_criar_insubsistencia_de_designacao(self):
        """Verifica criar insubsistencia de designacao."""
        d = criar_ato_designacao()
        ato = InsubsistenciaService.criar(_data(d))
        assert ato.pk is not None
        assert ato.ato_pai_id == d.pk

    def test_criar_insubsistencia_de_cessacao(self):
        """Verifica criar insubsistencia de cessacao."""
        d = criar_ato_designacao()
        c = criar_ato_cessacao(d)
        ato = InsubsistenciaService.criar(_data(c))
        assert ato.pk is not None
        assert (
            ato.status_publicacao
            == AtoAdministrativo.StatusPublicacao.NAO_PUBLICADO
        )

    def test_erro_ato_ja_insubsistente(self):
        """Verifica erro ato ja insubsistente."""
        d = criar_ato_designacao()
        InsubsistenciaService.criar(_data(d))
        d.refresh_from_db()
        with pytest.raises(ValidationError, match="insubsistente"):
            InsubsistenciaService.criar(_data(d))

    def test_erro_insubsistencia_duplicada(self):
        """Verifica erro insubsistencia duplicada."""
        d = criar_ato_designacao()
        criar_ato_insubsistencia(d)
        with pytest.raises(ValidationError):
            InsubsistenciaService.criar(_data(d))

    def test_tornar_sem_efeito_insubsistencia(self):
        """Verifica tornar sem efeito insubsistencia."""
        d = criar_ato_designacao()
        insub = InsubsistenciaService.criar(_data(d))
        d.refresh_from_db()
        assert not d.eh_valido

        InsubsistenciaService.criar(_data(insub, sei_numero="SEI-TSE"))
        d.refresh_from_db()
        assert d.eh_valido

    def test_insubsistencia_de_apostila_reverte_campos(self):
        """Verifica insubsistencia de apostila reverte campos."""
        d = criar_ato_designacao(numero_portaria="001")
        from apps.designacao.services.apostila_service import ApostilaService

        ApostilaService.criar(
            {
                "ato_pai": d,
                "sei_numero": "SEI-A",
                "observacao": "X",
                "alteracoes": [
                    {"campo_alterado": "numero_portaria", "valor_novo": "999"}
                ],
            }
        )
        d.refresh_from_db()
        assert d.numero_portaria == "999"

        ap = d.filhos.filter(tipo="APOSTILA").first()
        InsubsistenciaService.criar(_data(ap))

        d.refresh_from_db()
        assert d.numero_portaria == "001"

    def test_insubsistencia_de_designacao_reverte_apostilas_filhas(self):
        """Verifica insubsistencia de designacao reverte apostilas filhas."""
        d = criar_ato_designacao(numero_portaria="001")
        from apps.designacao.services.apostila_service import ApostilaService

        ApostilaService.criar(
            {
                "ato_pai": d,
                "sei_numero": "SEI-A",
                "observacao": "X",
                "alteracoes": [
                    {"campo_alterado": "numero_portaria", "valor_novo": "999"}
                ],
            }
        )
        d.refresh_from_db()
        assert d.numero_portaria == "999"

        InsubsistenciaService.criar(_data(d))

        d.refresh_from_db()
        assert d.numero_portaria == "001"

    def test_insubsistencia_de_designacao_anula_apostilas_ativas(self):
        """Verifica insubsistencia de designacao anula apostilas ativas."""
        from apps.designacao.models.ato_administrativo import AtoAdministrativo
        from apps.designacao.services.apostila_service import ApostilaService

        d = criar_ato_designacao()
        ApostilaService.criar(
            {
                "ato_pai": d,
                "sei_numero": "SEI-A",
                "observacao": "X",
                "alteracoes": [],
            }
        )
        apostila = d.filhos.filter(
            tipo=AtoAdministrativo.Tipo.APOSTILA
        ).first()
        assert apostila.ativo

        InsubsistenciaService.criar(_data(d))

        apostila.refresh_from_db()
        assert not apostila.ativo

    def test_insubsistencia_de_cessacao_anula_apostilas_da_cessacao(self):
        """Verifica insubsistencia de cessacao anula apostilas da cessacao."""
        from apps.designacao.services.apostila_service import ApostilaService

        d = criar_ato_designacao()
        c = criar_ato_cessacao(d)
        ApostilaService.criar(
            {
                "ato_pai": c,
                "sei_numero": "SEI-A",
                "observacao": "X",
                "alteracoes": [],
            }
        )
        apostila = c.filhos.filter(
            tipo=AtoAdministrativo.Tipo.APOSTILA
        ).first()
        assert apostila.ativo

        InsubsistenciaService.criar(_data(c))

        apostila.refresh_from_db()
        assert not apostila.ativo

    def test_insubsistencia_reverte_booleano_de_designacao_detalhe(self):
        """Verifica insubsistencia reverte booleano de designacao detalhe."""
        from apps.designacao.services.apostila_service import ApostilaService

        d = criar_ato_designacao()
        assert not d.designacao_detalhe.carater_excepcional

        ApostilaService.criar(
            {
                "ato_pai": d,
                "sei_numero": "SEI-B",
                "observacao": "X",
                "alteracoes": [
                    {
                        "campo_alterado": "carater_excepcional",
                        "valor_novo": "True",
                    }
                ],
            }
        )
        d.designacao_detalhe.refresh_from_db()
        assert d.designacao_detalhe.carater_excepcional

        InsubsistenciaService.criar(_data(d))

        d.designacao_detalhe.refresh_from_db()
        assert not d.designacao_detalhe.carater_excepcional

    def test_insubsistencia_reverte_booleano_de_cessacao_detalhe(self):
        """Verifica insubsistencia reverte booleano de cessacao detalhe."""
        from apps.designacao.services.apostila_service import ApostilaService

        d = criar_ato_designacao()
        c = criar_ato_cessacao(d)
        assert not c.cessacao_detalhe.a_pedido

        ApostilaService.criar(
            {
                "ato_pai": c,
                "sei_numero": "SEI-C",
                "observacao": "X",
                "alteracoes": [
                    {"campo_alterado": "a_pedido", "valor_novo": "True"}
                ],
            }
        )
        c.cessacao_detalhe.refresh_from_db()
        assert c.cessacao_detalhe.a_pedido

        InsubsistenciaService.criar(_data(c))

        c.cessacao_detalhe.refresh_from_db()
        assert not c.cessacao_detalhe.a_pedido

    def test_reverter_apostila_sem_detalhe_nao_falha(self):
        """Verifica que _reverter_apostila ignora ato sem apostila_detalhe."""
        d = criar_ato_designacao()

        InsubsistenciaService._reverter_apostila(d, d)

        d.refresh_from_db()
        assert d.numero_portaria

    def test_get_detalhe_retorna_none_para_apostila(self):
        """Verifica que _get_detalhe retorna None para tipos sem detalhe."""
        d = criar_ato_designacao()
        apostila = criar_ato_apostila(d)

        assert InsubsistenciaService._get_detalhe(apostila) is None

    def test_coerce_valor_retorna_valor_original_sem_campo(self):
        """Verifica que _coerce_valor retorna o valor original sem campo."""
        d = criar_ato_designacao()

        valor = InsubsistenciaService._coerce_valor(
            d, None, "campo_inexistente", "valor-bruto"
        )

        assert valor == "valor-bruto"

    def test_coerce_valor_retorna_none_para_string_vazia_em_campo_nulo(self):
        """Verifica que _coerce_valor retorna None para campo nulo vazio."""
        d = criar_ato_designacao()

        valor = InsubsistenciaService._coerce_valor(d, None, "doc", "")

        assert valor is None

    def test_coerce_valor_converte_inteiro(self):
        """Verifica que _coerce_valor converte campo inteiro."""
        d = criar_ato_designacao()

        valor = InsubsistenciaService._coerce_valor(
            d, d.designacao_detalhe, "cargo_vaga", "42"
        )

        assert valor == 42

    def test_coerce_valor_converte_float(self):
        """Verifica que _coerce_valor converte campo float."""
        detalhe = MagicMock()
        detalhe.peso = "12.5"
        detalhe._meta.get_field.return_value = FloatField(null=True)

        valor = InsubsistenciaService._coerce_valor(
            MagicMock(spec=[]), detalhe, "peso", "12.5"
        )

        assert valor == pytest.approx(12.5)

    def test_coerce_valor_retorna_original_em_erro_de_conversao(self):
        """Verifica que erro de conversão retorna o valor original."""
        d = criar_ato_designacao()

        valor = InsubsistenciaService._coerce_valor(
            d, d.designacao_detalhe, "cargo_vaga", "abc"
        )

        assert valor == "abc"
