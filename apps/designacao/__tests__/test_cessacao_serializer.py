"""Testes para serializer de cessação."""

import pytest

from apps.designacao.__tests__.factories import (
    criar_ato_cessacao,
    criar_ato_designacao,
    criar_ato_insubsistencia,
)
from apps.designacao.api.serializers.cessacao_serializer import (
    CessacaoReadSerializer,
    CessacaoReadSerializerById,
    CessacaoWriteSerializer,
)


@pytest.mark.django_db
class TestCessacaoWriteSerializer:
    """Testes para cessacao write serializer."""

    def _payload(self, ato_pai_id):
        """Método auxiliar para payload."""
        return {
            "ato_pai": ato_pai_id,
            "numero_portaria": "12345",
            "ano_vigente": "2024",
            "sei_numero": "999999",
            "a_pedido": True,
            "data_cessacao": "2024-03-10",
        }

    def test_serializer_valido(self):
        """Verifica serializer valido."""
        d = criar_ato_designacao()
        s = CessacaoWriteSerializer(data=self._payload(d.id))
        assert s.is_valid(), s.errors

    def test_numero_portaria_invalido(self):
        """Verifica numero portaria invalido."""
        d = criar_ato_designacao()
        payload = self._payload(d.id)
        payload["numero_portaria"] = "12A45"
        s = CessacaoWriteSerializer(data=payload)
        assert not s.is_valid()
        assert "numero_portaria" in s.errors

    def test_ano_vigente_invalido(self):
        """Verifica ano vigente invalido."""
        d = criar_ato_designacao()
        payload = self._payload(d.id)
        payload["ano_vigente"] = "20A4"
        s = CessacaoWriteSerializer(data=payload)
        assert not s.is_valid()
        assert "ano_vigente" in s.errors

    def test_ato_pai_invalido_rejeita(self):
        """Verifica ato pai invalido rejeita."""
        payload = self._payload(9999)
        s = CessacaoWriteSerializer(data=payload)
        assert not s.is_valid()
        assert "ato_pai" in s.errors


@pytest.mark.django_db
class TestCessacaoReadSerializer:
    """Testes para cessacao read serializer."""

    def test_get_insubsistencia_retorna_dados_quando_existe(self):
        """Verifica get insubsistencia retorna dados quando existe."""
        d = criar_ato_designacao()
        c = criar_ato_cessacao(d)
        insub = criar_ato_insubsistencia(c)

        # Simula o prefetch que a view faz
        from apps.designacao.models.ato_administrativo import AtoAdministrativo

        c_com_prefetch = (
            AtoAdministrativo.objects.filter(pk=c.pk)
            .prefetch_related("filhos", "filhos__insubsistencia_detalhe")
            .first()
        )
        data = CessacaoReadSerializer(c_com_prefetch).data

        assert data["insubsistencia"] is not None
        assert data["insubsistencia"]["id"] == insub.id

    def test_get_insubsistencia_retorna_none_quando_nao_existe(self):
        """Verifica get insubsistencia retorna none quando nao existe."""
        d = criar_ato_designacao()
        c = criar_ato_cessacao(d)

        from apps.designacao.models.ato_administrativo import AtoAdministrativo

        c_com_prefetch = (
            AtoAdministrativo.objects.filter(pk=c.pk)
            .prefetch_related("filhos", "filhos__insubsistencia_detalhe")
            .first()
        )
        data = CessacaoReadSerializer(c_com_prefetch).data

        assert data["insubsistencia"] is None


@pytest.mark.django_db
class TestCessacaoReadSerializerById:
    """Testes para cessacao read serializer by id."""

    def test_serializer_retorna_designacao_com_dados_do_ato_pai(self):
        """Verifica retorno de designacao no serializer by id."""
        designacao = criar_ato_designacao(
            numero_portaria="9876",
            ano_vigente="2025",
            sei_numero="SEI-DES",
        )
        cessacao = criar_ato_cessacao(
            designacao,
            a_pedido=True,
            remocao=True,
        )

        data = CessacaoReadSerializerById(cessacao).data

        assert "designacao" in data
        assert data["designacao"] is not None
        assert (
            data["designacao"]["numero_portaria"] == designacao.numero_portaria
        )
        assert data["designacao"]["ano_vigente"] == designacao.ano_vigente
        assert data["designacao"]["sei_numero"] == designacao.sei_numero
        assert data["designacao"]["portaria"] == designacao.numero_portaria

    def test_serializer_by_id_expoe_campo_designacao(self):
        """Verifica que serializer by id expõe o campo designacao."""
        designacao = criar_ato_designacao()
        cessacao = criar_ato_cessacao(designacao)

        data = CessacaoReadSerializerById(cessacao).data

        assert "designacao" in data
