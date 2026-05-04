import pytest
from django.test import TestCase

from apps.designacao.models.designacao import Designacao
from apps.designacao.models.cessacao import Cessacao
from apps.designacao.models.insubsistencia import Insubsistencia
from apps.designacao.api.serializers.cessacao_serializer import CessacaoSerializer
from apps.designacao.api.serializers.designacao_serializer import DesignacaoSerializer


class CessacaoSerializerTest(TestCase):

    def _criar_designacao(self):
        return Designacao.objects.create(
            dre_nome="DRE",
            unidade_proponente="Unidade",
            codigo_hierarquico="123",
            indicado_nome_civil="Nome",
            indicado_nome_servidor="Nome",
            indicado_rf="1234567",
            indicado_vinculo=1,
            indicado_cargo_base="Cargo",
            indicado_lotacao="Lotacao",
            indicado_local_exercicio="Local",
            numero_portaria="123",
            ano_vigente="2024",
            sei_numero="123",
            data_inicio="2024-01-01",
            tipo_vaga=Designacao.TipoVaga.VAGO,
        )

    @pytest.mark.django_db
    def test_serializer_valido(self):
        designacao = self._criar_designacao()

        data = {
            "designacao": designacao.id,
            "numero_portaria": "12345",
            "ano_vigente": "2024",
            "sei_numero": "999999",
            "a_pedido": True,
            "remocao": False,
            "aposentadoria": False,
            "doc": "DOE",
            "data_designacao": "2024-03-10"
        }

        serializer = CessacaoSerializer(data=data)

        assert serializer.is_valid(), serializer.errors


    @pytest.mark.django_db
    def test_numero_portaria_invalido(self):
        designacao = self._criar_designacao()

        data = {
            "designacao": designacao.id,
            "numero_portaria": "12A45",
            "ano_vigente": "2024",
            "sei_numero": "999999",
            "a_pedido": True,
            "data_designacao": "2024-03-10"
        }

        serializer = CessacaoSerializer(data=data)

        assert not serializer.is_valid()
        assert "numero_portaria" in serializer.errors


    @pytest.mark.django_db
    def test_ano_vigente_invalido(self):
        designacao = self._criar_designacao()

        data = {
            "designacao": designacao.id,
            "numero_portaria": "12345",
            "ano_vigente": "20A4",
            "sei_numero": "999999",
            "a_pedido": True,
            "data_designacao": "2024-03-10"
        }

        serializer = CessacaoSerializer(data=data)

        assert not serializer.is_valid()
        assert "ano_vigente" in serializer.errors


    @pytest.mark.django_db
    def test_nao_permite_cessacao_duplicada(self):
        designacao = self._criar_designacao()

        # cria primeira cessação
        Cessacao.objects.create(
            designacao=designacao,
            numero_portaria="12345",
            ano_vigente="2024",
            sei_numero="999999",
            a_pedido=True,
            data_designacao="2024-03-10"
        )

        data = {
            "designacao": designacao.id,
            "numero_portaria": "54321",
            "ano_vigente": "2024",
            "sei_numero": "888888",
            "a_pedido": True,
            "data_designacao": "2024-03-11"
        }

        serializer = CessacaoSerializer(data=data)

        assert not serializer.is_valid()
        assert "designacao" in serializer.errors


    @pytest.mark.django_db
    def test_get_insubsistencia_retorna_dados_quando_existe_insubsistencia_ativa(self):
        """
        Deve retornar os dados da insubsistência ativa vinculada à cessação.
        """
        designacao = self._criar_designacao()
        cessacao = Cessacao.objects.create(
            designacao=designacao,
            numero_portaria="12345",
            ano_vigente="2024",
            sei_numero="999999",
            data_designacao="2024-03-10",
        )
        insubsistencia = Insubsistencia.objects.create(
            cessacao=cessacao,
            numero_portaria="11111",
            ano_vigente="2024",
            sei_numero="888888",
        )

        serializer = CessacaoSerializer(instance=cessacao)

        assert serializer.data["insubsistencia"] is not None
        assert serializer.data["insubsistencia"]["id"] == insubsistencia.id

    @pytest.mark.django_db
    def test_designacao_nao_deve_exibir_cessacao_com_soft_delete(self):
        """
        Verifica se ao marcar uma cessação como is_deleted=True,
        ela para de aparecer na serialização da Designação.
        """
        designacao = self._criar_designacao()

        cessacao = Cessacao.objects.create(
            designacao=designacao,
            numero_portaria="12345",
            ano_vigente="2024",
            sei_numero="999999",
            data_designacao="2024-03-10"
        )

        serializer_antes = DesignacaoSerializer(instance=designacao)
        assert serializer_antes.data['cessacao'] is not None
        assert serializer_antes.data['cessacao']['id'] == cessacao.id

        cessacao.delete()
        
        designacao.refresh_from_db()

        serializer_depois = DesignacaoSerializer(instance=designacao)
        
        assert serializer_depois.data['cessacao'] is None, \
            "A cessação deveria ser nula no serializer após o soft delete."