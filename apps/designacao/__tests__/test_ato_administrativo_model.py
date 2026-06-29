"""Testes para o modelo de ato administrativo.

"""

import pytest
from django.core.exceptions import ValidationError

from apps.designacao.__tests__.factories import (
    criar_ato_apostila,
    criar_ato_cessacao,
    criar_ato_designacao,
    criar_ato_insubsistencia,
)
from apps.designacao.models.ato_administrativo import AtoAdministrativo

T = AtoAdministrativo.Tipo


@pytest.mark.django_db
class TestAtoAdministrativoStatus:
    """Testes para ato administrativo status."""

    def test_ativo_por_padrao(self):
        """Verifica ativo por padrao."""
        d = criar_ato_designacao()
        assert d.ativo is True

    def test_status_ativo(self):
        """Verifica status ativo."""
        d = criar_ato_designacao()
        assert d.status == "ativo"

    def test_status_insubsistente(self):
        """Verifica status insubsistente."""
        d = criar_ato_designacao()
        d.ativo = False
        d.save(update_fields=["ativo"])
        assert d.status == "insubsistente"

    def test_eh_valido_true(self):
        """Verifica eh valido true."""
        d = criar_ato_designacao()
        assert d.eh_valido is True

    def test_eh_valido_false(self):
        """Verifica eh valido false."""
        d = criar_ato_designacao()
        d.ativo = False
        d.save(update_fields=["ativo"])
        assert d.eh_valido is False

    def test_status_cessada_quando_possui_cessacao_ativa(self):
        """Verifica status cessada quando possui cessacao ativa."""
        d = criar_ato_designacao()
        criar_ato_cessacao(d)
        d.refresh_from_db()
        assert d.status == "cessada"

    def test_status_volta_para_ativo_quando_cessacao_insubsistida(self):
        """Verifica status volta para ativo quando cessacao insubsistida."""
        d = criar_ato_designacao()
        cessacao = criar_ato_cessacao(d)
        criar_ato_insubsistencia(cessacao)
        cessacao.ativo = False
        cessacao.save(update_fields=["ativo"])
        d.refresh_from_db()
        assert d.status == "ativo"

    def test_status_cessada_nao_afeta_eh_valido(self):
        """Verifica status cessada nao afeta eh valido."""
        d = criar_ato_designacao()
        criar_ato_cessacao(d)
        d.refresh_from_db()
        assert d.eh_valido is True


@pytest.mark.django_db
class TestAtoAdministrativoStatusPublicacao:
    """Testes para ato administrativo status publicação."""

    def test_status_publicacao(self):
        """Verifica status publicação."""
        d = criar_ato_designacao()
        assert (
            d.status_publicacao
            == AtoAdministrativo.StatusPublicacao.NAO_PUBLICADO
        )


@pytest.mark.django_db
class TestAtoAdministrativoAtoRaiz:
    """Testes para ato administrativo ato raiz."""

    def test_ato_raiz_nulo_em_designacao(self):
        """Verifica ato raiz nulo em designacao."""
        d = criar_ato_designacao()
        assert d.ato_raiz_id is None

    def test_ato_raiz_aponta_para_designacao_em_filho_direto(self):
        """Verifica ato raiz aponta para designacao em filho direto."""
        d = criar_ato_designacao()
        c = criar_ato_cessacao(d)
        assert c.ato_raiz_id == d.pk

    def test_ato_raiz_aponta_para_designacao_em_neto(self):
        """Verifica ato raiz aponta para designacao em neto."""
        d = criar_ato_designacao()
        c = criar_ato_cessacao(d)
        ap = criar_ato_apostila(c)
        assert ap.ato_raiz_id == d.pk

    def test_ato_raiz_nao_e_sobrescrito_se_ja_definido(self):
        """Verifica ato raiz nao e sobrescrito se ja definido."""
        d = criar_ato_designacao()
        c = criar_ato_cessacao(d)
        c.sei_numero = "SEI-UPDATED"
        c.save(update_fields=["sei_numero"])
        c.refresh_from_db()
        assert c.ato_raiz_id == d.pk


@pytest.mark.django_db
class TestAtoAdministrativoCleanHierarquia:
    """Testes para ato administrativo clean hierarquia."""

    def test_cessacao_com_pai_designacao_e_valida(self):
        """Verifica cessacao com pai designacao e valida."""
        d = criar_ato_designacao()
        c = criar_ato_cessacao(d)
        assert c.pk is not None

    def test_apostila_com_pai_designacao_e_valida(self):
        """Verifica apostila com pai designacao e valida."""
        d = criar_ato_designacao()
        ap = criar_ato_apostila(d)
        assert ap.pk is not None

    def test_apostila_com_pai_cessacao_e_valida(self):
        """Verifica apostila com pai cessacao e valida."""
        d = criar_ato_designacao()
        c = criar_ato_cessacao(d)
        ap = criar_ato_apostila(c)
        assert ap.pk is not None

    def test_insubsistencia_com_pai_designacao_e_valida(self):
        """Verifica insubsistencia com pai designacao e valida."""
        d = criar_ato_designacao()
        i = criar_ato_insubsistencia(d)
        assert i.pk is not None

    def test_insubsistencia_com_pai_cessacao_e_valida(self):
        """Verifica insubsistencia com pai cessacao e valida."""
        d = criar_ato_designacao()
        c = criar_ato_cessacao(d)
        i = criar_ato_insubsistencia(c)
        assert i.pk is not None

    def test_insubsistencia_com_pai_apostila_e_valida(self):
        """Verifica insubsistencia com pai apostila e valida."""
        d = criar_ato_designacao()
        ap = criar_ato_apostila(d)
        i = criar_ato_insubsistencia(ap)
        assert i.pk is not None

    def test_insubsistencia_com_pai_insubsistencia_e_valida(self):
        """Verifica insubsistencia com pai insubsistencia e valida."""
        d = criar_ato_designacao()
        i1 = criar_ato_insubsistencia(d)
        i2 = criar_ato_insubsistencia(i1)
        assert i2.pk is not None

    def test_designacao_sem_pai_e_valida(self):
        """Verifica designacao sem pai e valida."""
        d = criar_ato_designacao()
        assert d.ato_pai_id is None

    def test_cessacao_sem_pai_levanta_erro(self):
        """Verifica cessacao sem pai levanta erro."""
        with pytest.raises(ValidationError, match="precisa de um ato pai"):
            AtoAdministrativo.objects.create(
                tipo=T.CESSACAO,
                sei_numero="SEI-X",
            )

    def test_cessacao_com_pai_cessacao_levanta_erro(self):
        """Verifica cessacao com pai cessacao levanta erro."""
        d = criar_ato_designacao()
        c = criar_ato_cessacao(d)
        with pytest.raises(ValidationError, match="não pode ter"):
            AtoAdministrativo.objects.create(
                tipo=T.CESSACAO,
                ato_pai=c,
                sei_numero="SEI-X",
                numero_portaria="001",
                ano_vigente="2024",
            )

    def test_apostila_com_pai_insubsistencia_levanta_erro(self):
        """Verifica apostila com pai insubsistencia levanta erro."""
        d = criar_ato_designacao()
        i = criar_ato_insubsistencia(d)
        with pytest.raises(ValidationError, match="não pode ter"):
            AtoAdministrativo.objects.create(
                tipo=T.APOSTILA,
                ato_pai=i,
                sei_numero="SEI-X",
            )

    def test_designacao_com_pai_levanta_erro(self):
        """Verifica designacao com pai levanta erro."""
        d = criar_ato_designacao()
        with pytest.raises(ValidationError):
            AtoAdministrativo.objects.create(
                tipo=T.DESIGNACAO,
                ato_pai=d,
                sei_numero="SEI-X",
                numero_portaria="001",
                ano_vigente="2024",
            )


@pytest.mark.django_db
class TestAtoAdministrativoCleanCessacaoUnica:
    """Testes para ato administrativo clean cessacao unica."""

    def test_bloqueia_segunda_cessacao_ativa(self):
        """Verifica bloqueia segunda cessacao ativa."""
        d = criar_ato_designacao()
        criar_ato_cessacao(d)
        with pytest.raises(ValidationError, match="cessação ativa"):
            AtoAdministrativo.objects.create(
                tipo=T.CESSACAO,
                ato_pai=d,
                sei_numero="SEI-C2",
                numero_portaria="002",
                ano_vigente="2024",
            )

    def test_permite_segunda_cessacao_apos_insubsistir_primeira(self):
        """Verifica permite segunda cessacao apos insubsistir primeira."""
        d = criar_ato_designacao()
        c1 = criar_ato_cessacao(d)
        c1.ativo = False
        c1.save(update_fields=["ativo"])

        c2 = criar_ato_cessacao(d, sei_numero="SEI-C2", numero_portaria="002")
        assert c2.pk is not None
