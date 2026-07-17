"""Testes para o serializer de leitura de designação.

Cobre a serialização de atos filhos (cessação, apostilas, insubsistência)
e os fallbacks de exceção dos campos derivados de designacao_detalhe.
"""

import pytest

from apps.designacao.__tests__.factories import (
    criar_ato_apostila,
    criar_ato_cessacao,
    criar_ato_designacao,
    criar_ato_insubsistencia,
)
from apps.designacao.api.serializers.designacao_serializer import (
    DesignacaoReadSerializer,
)
from apps.designacao.models.ato_administrativo import AtoAdministrativo


def _buscar(pk: int) -> AtoAdministrativo:
    """Busca o ato do zero no banco, sem cache de instância em memória."""
    return AtoAdministrativo.objects.get(pk=pk)


@pytest.mark.django_db
class TestDesignacaoReadSerializerCessacao:
    """Testes do campo derivado `cessacao`."""

    def test_none_quando_nao_existe_cessacao(self):
        """Verifica none quando nao existe cessacao."""
        d = criar_ato_designacao()

        data = DesignacaoReadSerializer(_buscar(d.pk)).data

        assert data["cessacao"] is None

    def test_retorna_dados_com_apostilas_e_insubsistencia_da_cessacao(self):
        """Verifica retorna dados com apostilas e insubsistencia da cessacao."""
        d = criar_ato_designacao()
        c = criar_ato_cessacao(d)
        criar_ato_apostila(c, observacao="Retificação de cessação")
        insub = criar_ato_insubsistencia(c, observacoes="Motivo cessação")

        data = DesignacaoReadSerializer(_buscar(d.pk)).data

        assert data["cessacao"]["id"] == c.id
        assert data["cessacao"]["numero_portaria"] == c.numero_portaria
        assert data["cessacao"]["ano_vigente"] == c.ano_vigente
        assert data["cessacao"]["a_pedido"] is False
        assert data["cessacao"]["remocao"] is False
        assert data["cessacao"]["aposentadoria"] is False
        assert len(data["cessacao"]["apostilas"]) == 1
        assert (
            data["cessacao"]["apostilas"][0]["observacao"]
            == "Retificação de cessação"
        )
        assert data["cessacao"]["insubsistencia"]["id"] == insub.id
        assert data["cessacao"]["insubsistencia"]["observacoes"] == (
            "Motivo cessação"
        )

    def test_retorna_none_quando_cessacao_sem_detalhe(self):
        """Verifica none em erro (cessação sem CessacaoDetalhe)."""
        d = criar_ato_designacao()
        AtoAdministrativo.objects.create(
            tipo=AtoAdministrativo.Tipo.CESSACAO,
            ato_pai=d,
            numero_portaria="456",
            ano_vigente="2024",
            sei_numero="SEI-CESSACAO",
        )

        data = DesignacaoReadSerializer(_buscar(d.pk)).data

        assert data["cessacao"] is None

    def test_cessacao_sem_apostilas_nem_insubsistencia(self):
        """Verifica cessação sem apostilas nem insubsistência ativas."""
        d = criar_ato_designacao()
        criar_ato_cessacao(d)

        data = DesignacaoReadSerializer(_buscar(d.pk)).data

        assert data["cessacao"]["apostilas"] == []
        assert data["cessacao"]["insubsistencia"] is None

    def test_cessacao_com_insubsistencia_sem_detalhe(self):
        """Verifica none quando a insubsistência da cessação não tem detalhe."""
        d = criar_ato_designacao()
        c = criar_ato_cessacao(d)
        AtoAdministrativo.objects.create(
            tipo=AtoAdministrativo.Tipo.INSUBSISTENCIA,
            ato_pai=c,
            numero_portaria="789",
            ano_vigente="2024",
            sei_numero="SEI-INSUB-CESSACAO",
        )

        data = DesignacaoReadSerializer(_buscar(d.pk)).data

        assert data["cessacao"]["insubsistencia"] is None


@pytest.mark.django_db
class TestDesignacaoReadSerializerApostilas:
    """Testes do campo derivado `apostilas`."""

    def test_lista_vazia_quando_sem_apostilas(self):
        """Verifica lista vazia quando sem apostilas."""
        d = criar_ato_designacao()

        data = DesignacaoReadSerializer(_buscar(d.pk)).data

        assert data["apostilas"] == []

    def test_ignora_apostila_insubsistente_e_sem_detalhe(self):
        """Verifica que apostila insubsistente e sem detalhe são ignoradas."""
        d = criar_ato_designacao()
        ativa = criar_ato_apostila(d, observacao="Ativa")

        insubsistente = criar_ato_apostila(d, observacao="Insubsistente")
        insubsistente.ativo = False
        insubsistente.save(update_fields=["ativo"])

        AtoAdministrativo.objects.create(
            tipo=AtoAdministrativo.Tipo.APOSTILA,
            ato_pai=d,
            sei_numero="SEI-SEM-DETALHE",
        )

        data = DesignacaoReadSerializer(_buscar(d.pk)).data

        assert [a["id"] for a in data["apostilas"]] == [ativa.id]
        assert data["apostilas"][0]["observacao"] == "Ativa"


@pytest.mark.django_db
class TestDesignacaoReadSerializerInsubsistencia:
    """Testes do campo derivado `insubsistencia` (da própria designação)."""

    def test_none_quando_nao_existe_insubsistencia(self):
        """Verifica none quando nao existe insubsistencia."""
        d = criar_ato_designacao()

        data = DesignacaoReadSerializer(_buscar(d.pk)).data

        assert data["insubsistencia"] is None

    def test_none_quando_insubsistencia_inativa(self):
        """Verifica none quando a insubsistência já foi tornada sem efeito."""
        d = criar_ato_designacao()
        insub = criar_ato_insubsistencia(d)
        insub.ativo = False
        insub.save(update_fields=["ativo"])

        data = DesignacaoReadSerializer(_buscar(d.pk)).data

        assert data["insubsistencia"] is None

    def test_retorna_dados_da_insubsistencia_ativa(self):
        """Verifica retorna dados da insubsistência ativa."""
        d = criar_ato_designacao()
        insub = criar_ato_insubsistencia(d, observacoes="Erro material")

        data = DesignacaoReadSerializer(_buscar(d.pk)).data

        assert data["insubsistencia"]["id"] == insub.id
        assert (
            data["insubsistencia"]["numero_portaria"] == insub.numero_portaria
        )
        assert data["insubsistencia"]["observacoes"] == "Erro material"

    def test_retorna_none_quando_insubsistencia_sem_detalhe(self):
        """Verifica none em erro (insubsistência sem InsubsistenciaDetalhe)."""
        d = criar_ato_designacao()
        AtoAdministrativo.objects.create(
            tipo=AtoAdministrativo.Tipo.INSUBSISTENCIA,
            ato_pai=d,
            numero_portaria="789",
            ano_vigente="2024",
            sei_numero="SEI-INSUB",
        )

        data = DesignacaoReadSerializer(_buscar(d.pk)).data

        assert data["insubsistencia"] is None


@pytest.mark.django_db
class TestDesignacaoReadSerializerDisplaysSemDetalhe:
    """Testes dos fallbacks de exceção quando não há designacao_detalhe."""

    def test_displays_retornam_none_sem_designacao_detalhe(self):
        """Verifica que os campos *_display voltam None sem detalhe."""
        ato = AtoAdministrativo.objects.create(
            tipo=AtoAdministrativo.Tipo.DESIGNACAO,
            numero_portaria="001",
            ano_vigente="2024",
            sei_numero="SEI-SEM-DETALHE",
        )

        data = DesignacaoReadSerializer(_buscar(ato.pk)).data

        assert data["impedimento_display"] is None
        assert data["tipo_vaga_display"] is None
        assert data["cargo_vaga_display"] is None
