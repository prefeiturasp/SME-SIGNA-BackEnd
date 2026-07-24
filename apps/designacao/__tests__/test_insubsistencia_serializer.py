"""Testes para serializer de insubsistencia."""

import datetime
from types import SimpleNamespace

import pytest

from apps.designacao.__tests__.factories import (
    criar_ato_apostila,
    criar_ato_cessacao,
    criar_ato_designacao,
    criar_ato_insubsistencia,
)
from apps.designacao.api.serializers.insubsistencia_serializer import (
    InsubsistenciaReadSerializer,
    InsubsistenciaWriteSerializer,
)


@pytest.mark.django_db
class TestInsubsistenciaWriteSerializer:
    """Testes para insubsistencia write serializer."""

    def _payload(self, ato_pai_id):
        """Metodo auxiliar para payload."""
        return {
            "ato_pai": ato_pai_id,
            "numero_portaria": "12345",
            "ano_vigente": "2024",
            "sei_numero": "SEI-INSUB-1",
            "doc": "2024-03-10",
            "observacoes": "Erro material",
            "texto_apostila": "",
        }

    def test_serializer_valido(self):
        """Verifica serializer valido."""
        d = criar_ato_designacao()
        s = InsubsistenciaWriteSerializer(data=self._payload(d.id))
        assert s.is_valid(), s.errors

    def test_numero_portaria_invalido(self):
        """Verifica numero portaria invalido."""
        d = criar_ato_designacao()
        payload = self._payload(d.id)
        payload["numero_portaria"] = "12A45"
        s = InsubsistenciaWriteSerializer(data=payload)
        assert not s.is_valid()
        assert "numero_portaria" in s.errors

    def test_ano_vigente_invalido(self):
        """Verifica ano vigente invalido."""
        d = criar_ato_designacao()
        payload = self._payload(d.id)
        payload["ano_vigente"] = "20A4"
        s = InsubsistenciaWriteSerializer(data=payload)
        assert not s.is_valid()
        assert "ano_vigente" in s.errors

    def test_ato_pai_invalido_rejeita(self):
        """Verifica ato pai invalido rejeita."""
        s = InsubsistenciaWriteSerializer(data=self._payload(9999))
        assert not s.is_valid()
        assert "ato_pai" in s.errors


@pytest.mark.django_db
class TestInsubsistenciaReadSerializer:
    """Testes para insubsistencia read serializer."""

    def test_retorna_texto_apostila_quando_insubsistencia_de_apostila(self):
        """Verifica retorno do texto_apostila quando existir detalhe."""
        designacao = criar_ato_designacao()
        apostila = criar_ato_apostila(designacao)
        insubsistencia = criar_ato_insubsistencia(
            apostila,
            texto_apostila="Tornar sem efeito apostila",
            observacoes="Anulada",
        )

        data = InsubsistenciaReadSerializer(insubsistencia).data

        assert data["texto_apostila"] == "Tornar sem efeito apostila"
        assert data["tipo_insubsistencia"] == "APOSTILA"
        assert data["ato_apostilado"] == "DESIGNACAO"

    def test_retorna_none_em_campos_de_apostila_quando_nao_for_apostila(self):
        """Verifica campos de apostila nulos quando nao aplicavel."""
        designacao = criar_ato_designacao()
        insubsistencia = criar_ato_insubsistencia(designacao)

        data = InsubsistenciaReadSerializer(insubsistencia).data

        assert data["texto_apostila"] is None
        assert data["ato_apostilado"] is None
        assert data["tipo_insubsistencia"] == "DESIGNACAO"

    def test_get_insubsistencia_retorna_dados_quando_ato_pai_e_insubsistencia(
        self,
    ):
        """Verifica get insubsistencia quando ato pai e insubsistencia."""
        designacao = criar_ato_designacao(doc=datetime.date(2024, 1, 15))
        insubsistencia_pai = criar_ato_insubsistencia(
            designacao,
            numero_portaria="111",
            ano_vigente="2024",
            sei_numero="SEI-INSUB-PAI",
            doc=datetime.date(2024, 2, 10),
        )
        insubsistencia_filha = criar_ato_insubsistencia(
            insubsistencia_pai,
            numero_portaria="222",
            ano_vigente="2025",
            sei_numero="SEI-INSUB-FILHA",
        )

        data = InsubsistenciaReadSerializer(insubsistencia_filha).data

        assert data["insubsistencia"] is not None
        assert data["insubsistencia"]["numero_portaria"] == "111"
        assert data["insubsistencia"]["ano_vigente"] == "2024"
        assert data["insubsistencia"]["sei_numero"] == "SEI-INSUB-PAI"
        assert data["insubsistencia"]["doc"] == insubsistencia_pai.doc
        assert (
            data["insubsistencia"]["doc_do_ato_insubstituido"]
            == designacao.doc
        )

    def test_get_insubsistencia_retorna_none_quando_ato_pai_nao_insubsistencia(
        self,
    ):
        """Verifica get insubsistencia retorna none quando nao aplicavel."""
        designacao = criar_ato_designacao()
        insubsistencia = criar_ato_insubsistencia(designacao)

        data = InsubsistenciaReadSerializer(insubsistencia).data

        assert data["insubsistencia"] is None

    def test_retorna_dados_de_cessacao_quando_ato_pai_e_cessacao(self):
        """Verifica retorno de dados de cessacao em insubsistencia."""
        designacao = criar_ato_designacao()
        cessacao = criar_ato_cessacao(designacao, a_pedido=True, remocao=True)
        insubsistencia = criar_ato_insubsistencia(cessacao)

        data = InsubsistenciaReadSerializer(insubsistencia).data

        assert data["cessacao"] is not None
        assert data["cessacao"]["numero_portaria"] == cessacao.numero_portaria
        assert data["cessacao"]["a_pedido"] is True
        assert data["cessacao"]["remocao"] is True

    def test_get_tipo_insubsistencia_retorna_none_quando_nao_ha_ato_pai(self):
        """Verifica get tipo insubsistencia retorna none sem ato pai."""
        insubsistencia_sem_pai = SimpleNamespace(ato_pai=None)

        serializer = InsubsistenciaReadSerializer()

        assert (
            serializer.get_tipo_insubsistencia(insubsistencia_sem_pai) is None
        )

    def test_get_ato_apostilado_retorna_avo_quando_existe(self):
        """Verifica retorno do ato apostilado quando hierarquia existe."""
        designacao = criar_ato_designacao()
        apostila = criar_ato_apostila(designacao)
        insubsistencia = criar_ato_insubsistencia(apostila)

        serializer = InsubsistenciaReadSerializer()

        assert serializer._get_ato_apostilado(insubsistencia) == designacao

    def test_get_ato_apostilado_retorna_none_quando_nao_existe_avo(self):
        """Verifica retorno none quando nao existir avo para apostilamento."""
        designacao = criar_ato_designacao()
        insubsistencia = criar_ato_insubsistencia(designacao)

        serializer = InsubsistenciaReadSerializer()

        assert serializer._get_ato_apostilado(insubsistencia) is None
