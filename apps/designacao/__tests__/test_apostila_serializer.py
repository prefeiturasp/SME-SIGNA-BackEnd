"""Testes para serializer de apostila."""

import pytest

from apps.designacao.__tests__.factories import (
    criar_ato_apostila,
    criar_ato_cessacao,
    criar_ato_designacao,
    criar_ato_insubsistencia,
)
from apps.designacao.api.serializers.apostila_serializer import (
    ApostilaReadSerializer,
    ApostilaWriteSerializer,
)
from apps.designacao.models.apostila_detalhe import ApostilaAlteracao
from apps.designacao.models.ato_administrativo import AtoAdministrativo


@pytest.mark.django_db
class TestApostilaWriteSerializer:
    """Testes para apostila write serializer."""

    def _payload(self, ato_pai_id):
        """Método auxiliar para payload."""
        return {
            "ato_pai": ato_pai_id,
            "sei_numero": "SEI-AP-123",
            "observacao": "Texto de observação",
            "alteracoes": [
                {
                    "campo_alterado": "numero_portaria",
                    "valor_novo": "9999",
                }
            ],
        }

    def test_serializer_valido_com_designacao(self):
        """Verifica serializer valido com ato pai designacao."""
        designacao = criar_ato_designacao()
        serializer = ApostilaWriteSerializer(data=self._payload(designacao.id))
        assert serializer.is_valid(), serializer.errors

    def test_serializer_valido_com_cessacao(self):
        """Verifica serializer valido com ato pai cessacao."""
        designacao = criar_ato_designacao()
        cessacao = criar_ato_cessacao(designacao)
        serializer = ApostilaWriteSerializer(data=self._payload(cessacao.id))
        assert serializer.is_valid(), serializer.errors

    def test_ato_pai_invalido_rejeita(self):
        """Verifica ato pai invalido rejeita."""
        serializer = ApostilaWriteSerializer(data=self._payload(9999))
        assert not serializer.is_valid()
        assert "ato_pai" in serializer.errors

    def test_ato_pai_tipo_invalido_rejeita(self):
        """Verifica ato pai de tipo invalido rejeita."""
        designacao = criar_ato_designacao()
        insubsistencia = criar_ato_insubsistencia(designacao)

        serializer = ApostilaWriteSerializer(
            data=self._payload(insubsistencia.id)
        )
        assert not serializer.is_valid()
        assert "ato_pai" in serializer.errors

    def test_alteracoes_com_item_invalido_rejeita(self):
        """Verifica alteracoes com item invalido rejeita."""
        designacao = criar_ato_designacao()
        payload = self._payload(designacao.id)
        payload["alteracoes"] = [{"campo_alterado": "numero_portaria"}]

        serializer = ApostilaWriteSerializer(data=payload)
        assert not serializer.is_valid()
        assert "alteracoes" in serializer.errors

    def test_alteracoes_aceita_tipo_ato_alvo_opcional(self):
        """Verifica que tipo_ato_alvo é aceito e tem default vazio."""
        designacao = criar_ato_designacao()
        cessacao = criar_ato_cessacao(designacao)
        payload = self._payload(cessacao.id)
        payload["alteracoes"][0]["tipo_ato_alvo"] = "DESIGNACAO"

        serializer = ApostilaWriteSerializer(data=payload)
        assert serializer.is_valid(), serializer.errors
        assert (
            serializer.validated_data["alteracoes"][0]["tipo_ato_alvo"]
            == "DESIGNACAO"
        )

        payload_sem_alvo = self._payload(cessacao.id)
        serializer_sem_alvo = ApostilaWriteSerializer(data=payload_sem_alvo)
        assert serializer_sem_alvo.is_valid(), serializer_sem_alvo.errors
        assert (
            serializer_sem_alvo.validated_data["alteracoes"][0][
                "tipo_ato_alvo"
            ]
            == ""
        )

    def test_alteracoes_rejeita_tipo_ato_alvo_invalido(self):
        """Verifica que um tipo_ato_alvo fora do enum é rejeitado."""
        designacao = criar_ato_designacao()
        payload = self._payload(designacao.id)
        payload["alteracoes"][0]["tipo_ato_alvo"] = "NAO_EXISTE"

        serializer = ApostilaWriteSerializer(data=payload)
        assert not serializer.is_valid()
        assert "alteracoes" in serializer.errors


@pytest.mark.django_db
class TestApostilaReadSerializer:
    """Testes para apostila read serializer."""

    def test_get_insubsistencia_retorna_dados_quando_existe(self):
        """Verifica get insubsistencia retorna dados quando existe."""
        designacao = criar_ato_designacao()
        apostila = criar_ato_apostila(designacao)
        insubsistencia = criar_ato_insubsistencia(
            apostila, observacoes="Tornada sem efeito"
        )

        apostila_com_prefetch = (
            AtoAdministrativo.objects.filter(pk=apostila.pk)
            .prefetch_related("filhos", "filhos__insubsistencia_detalhe")
            .first()
        )

        data = ApostilaReadSerializer(apostila_com_prefetch).data

        assert data["insubsistencia"] is not None
        assert data["insubsistencia"]["id"] == insubsistencia.id
        assert data["insubsistencia"]["observacoes"] == "Tornada sem efeito"

    def test_get_insubsistencia_retorna_none_quando_nao_existe(self):
        """Verifica get insubsistencia retorna none quando nao existe."""
        designacao = criar_ato_designacao()
        apostila = criar_ato_apostila(designacao)
        data = ApostilaReadSerializer(apostila).data
        assert data["insubsistencia"] is None

    def test_get_alteracoes_retorna_lista_quando_existem_registros(self):
        """Verifica get alteracoes retorna lista quando existem registros."""
        designacao = criar_ato_designacao(numero_portaria=100)
        apostila = criar_ato_apostila(designacao)

        ApostilaAlteracao.objects.create(
            apostila=apostila.apostila_detalhe,
            ato_alterado=designacao,
            campo_alterado="numero_portaria",
            valor_anterior="100",
            valor_novo="200",
        )

        data = ApostilaReadSerializer(apostila).data

        assert len(data["alteracoes"]) == 1
        assert data["alteracoes"][0]["campo_alterado"] == "numero_portaria"
        assert data["alteracoes"][0]["valor_anterior"] == "100"
        assert data["alteracoes"][0]["valor_novo"] == "200"
        assert data["alteracoes"][0]["ato_alterado_id"] == designacao.id
        assert (
            data["alteracoes"][0]["ato_alterado_tipo"]
            == AtoAdministrativo.Tipo.DESIGNACAO
        )

    def test_serializer_retorna_dados_do_ato_apostilado_designacao(self):
        """Verifica serializer retorna dados do ato apostilado designacao."""
        designacao = criar_ato_designacao()
        apostila = criar_ato_apostila(designacao)

        data = ApostilaReadSerializer(apostila).data

        assert data["ato_apostilado"] == AtoAdministrativo.Tipo.DESIGNACAO
        assert data["ato_apostilado_display"] == "Designação"
        assert data["designacao"] is not None
        assert data["cessacao"] is None

    def test_get_alteracoes_retorna_lista_vazia_quando_sem_detalhe(self):
        """Verifica get alteracoes retorna lista vazia em erro inesperado."""
        designacao = criar_ato_designacao()
        apostila = criar_ato_apostila(designacao)
        apostila.apostila_detalhe.delete()
        apostila = AtoAdministrativo.objects.get(pk=apostila.pk)

        data = ApostilaReadSerializer(apostila).data

        assert data["alteracoes"] == []

    def test_get_insubsistencia_retorna_none_quando_erro_inesperado(self):
        """Verifica get insubsistencia retorna none quando falha ao acessar detalhe."""
        designacao = criar_ato_designacao()
        apostila = criar_ato_apostila(designacao)
        AtoAdministrativo.objects.create(
            tipo=AtoAdministrativo.Tipo.INSUBSISTENCIA,
            ato_pai=apostila,
            sei_numero="SEI-INS-SEM-DETALHE",
        )

        apostila_com_prefetch = (
            AtoAdministrativo.objects.filter(pk=apostila.pk)
            .prefetch_related("filhos", "filhos__insubsistencia_detalhe")
            .first()
        )

        data = ApostilaReadSerializer(apostila_com_prefetch).data

        assert data["insubsistencia"] is None

    def test_get_ato_apostilado_retorna_none_sem_ato_pai(self):
        """Verifica ato_apostilado e display retornam None sem ato pai.

        Usa instância não salva, já que o model exige ato_pai para
        APOSTILA na persistência — o branch defensivo do serializer
        continua existindo e precisa ser exercitado diretamente.
        """
        apostila_sem_pai = AtoAdministrativo(
            tipo=AtoAdministrativo.Tipo.APOSTILA, sei_numero="SEI-SEM-PAI"
        )
        serializer = ApostilaReadSerializer()

        assert serializer.get_ato_apostilado(apostila_sem_pai) is None
        assert serializer.get_ato_apostilado_display(apostila_sem_pai) is None

    def test_get_tipo_de_ato(self):
        """Verifica get_tipo_de_ato com e sem ato pai."""
        designacao = criar_ato_designacao()
        apostila = criar_ato_apostila(designacao)
        apostila_sem_pai = AtoAdministrativo(
            tipo=AtoAdministrativo.Tipo.APOSTILA, sei_numero="SEI-SEM-PAI-2"
        )

        serializer = ApostilaReadSerializer()

        assert serializer.get_tipo_de_ato(apostila) == "Apostila de Designação"
        assert serializer.get_tipo_de_ato(apostila_sem_pai) == "Apostila"
