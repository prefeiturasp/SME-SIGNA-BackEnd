"""Testes para serializers de apostila.

"""

import pytest

from django.utils import timezone

from apps.designacao.api.serializers.apostila_serializer import ApostilaSerializer
from apps.designacao.models.apostila import Apostila
from apps.designacao.models.cessacao import Cessacao
from apps.designacao.models.designacao import Designacao


@pytest.mark.django_db
class TestApostilaSerializer:
    """Testes para apostila serializer."""

    @pytest.fixture
    def designacao(self):
        """Método designacao."""
        return Designacao.objects.create(
            dre_nome="DRE TESTE",
            unidade_proponente="EMEF",
            codigo_hierarquico="1",
            indicado_nome_civil="USER",
            indicado_nome_servidor="USER",
            indicado_rf="1234567",
            indicado_vinculo=1,
            indicado_cargo_base="PROF",
            indicado_lotacao="L",
            indicado_local_exercicio="L",
            numero_portaria="123",
            ano_vigente="2026",
            sei_numero="111",
            data_inicio=timezone.now().date(),
            tipo_vaga=Designacao.TipoVaga.DISPONIVEL,
        )

    @pytest.fixture
    def apostila(self, designacao):
        """Método apostila."""
        return Apostila.objects.create(
            tipo=Apostila.Tipo.APOSTILA,
            designacao=designacao,
            sei_numero="555",
            observacao="Obs Teste",
            d_o="2026-01-01",
        )

    def test_serialization_campos_reais(self, apostila):
        """Verifica serialization campos reais."""
        serializer = ApostilaSerializer(instance=apostila)
        data = serializer.data
        assert data["id"] == apostila.id
        assert data["sei_numero"] == "555"
        assert "tipo" in data

    def test_deserialization_e_validacao(self, designacao):
        """Verifica deserialization e validacao."""
        input_data = {
            "designacao": designacao.id,
            "ato_apostilado": "designacao",
            "tipo": Apostila.Tipo.APOSTILA,
            "sei_numero": "999",
            "observacao": "Teste",
        }
        serializer = ApostilaSerializer(data=input_data)
        assert serializer.is_valid(), serializer.errors
        assert serializer.validated_data["designacao"] == designacao.id

    def test_to_representation_com_cessacao(self, designacao):
        """Verifica to representation com cessacao."""
        cessacao = Cessacao.objects.create(
            designacao=designacao,
            numero_portaria="456",
            ano_vigente="2026",
            sei_numero="222",
            data_designacao=timezone.now().date(),
        )
        apostila_cessacao = Apostila.objects.create(
            tipo=Apostila.Tipo.APOSTILA,
            cessacao=cessacao,
            sei_numero="777",
        )
        serializer = ApostilaSerializer(instance=apostila_cessacao)
        assert serializer.data["sei_numero"] == "777"

    def test_validacao_erro_vazio(self):
        """Verifica validacao erro vazio."""
        serializer = ApostilaSerializer(data={})
        assert not serializer.is_valid()
        assert len(serializer.errors) > 0

    def test_apostila_anulacao(self, designacao, apostila):
        """Verifica apostila anulacao."""
        apostila_anulacao = Apostila.objects.create(
            tipo=Apostila.Tipo.ANULACAO,
            designacao=designacao,
            apostila_referencia=apostila,
            sei_numero="888",
        )
        serializer = ApostilaSerializer(instance=apostila_anulacao)
        assert "tipo" in serializer.data
