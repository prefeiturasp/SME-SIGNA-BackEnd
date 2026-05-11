import pytest
from django.test import TestCase
from rest_framework import serializers as drf_serializers

from apps.designacao.models.designacao import Designacao
from apps.designacao.models.cessacao import Cessacao
from apps.designacao.api.serializers.cessacao_serializer import CessacaoSerializer
from apps.designacao.api.serializers.designacao_serializer import DesignacaoSerializer
from apps.designacao.api.serializers.insubsistencia_serializer import InsubsistenciaSerializer
from apps.designacao.__tests__.factories import criar_designacao_legado
from apps.designacao.models.insubsistencia import Insubsistencia, TipoInsubsistencia


class InsubsistenciaSerializerTest(TestCase):

    def _criar_designacao(self):
        return criar_designacao_legado()

    @pytest.mark.django_db
    def test_serializer_valido_na_designacao(self):
        designacao = self._criar_designacao()

        data = {
            "designacao": designacao.id,
            "numero_portaria": "12345",
            "ano_vigente": "2024",
            "sei_numero": "999999",             
            "doc": "DOE",
            "observacoes":"44444",
            "tipo_insubsistencia":"designacao"
        }

        serializer = InsubsistenciaSerializer(data=data)

        assert serializer.is_valid(), serializer.errors


    @pytest.mark.django_db
    def test_serializer_valido_na_cessacao(self):
        designacao = self._criar_designacao()

        cessacao = Cessacao.objects.create(
            designacao=designacao,
            numero_portaria="12345",
            ano_vigente="2024",
            sei_numero="999999",             
            doc="DOE",
            data_designacao="2024-03-10"
        )

        data = {
            "designacao": designacao.id,
            "numero_portaria": "12345",
            "ano_vigente": "2024",
            "sei_numero": "999999",             
            "doc": "DOE",
            "observacoes":"44444",
            "tipo_insubsistencia":"cessacao"
        }

        serializer = InsubsistenciaSerializer(data=data)

        assert serializer.is_valid(), serializer.errors




    @pytest.mark.django_db
    def test_serializer_valido_na_designacao_com_cessacao_sem_insubsistencia(self):
        designacao = self._criar_designacao()

        Cessacao.objects.create(
            designacao=designacao,
            numero_portaria="12345",
            ano_vigente="2024",
            sei_numero="999999",             
            doc="DOE",
            data_designacao="2024-03-10"
        )

        data = {
            "designacao": designacao.id,
            "numero_portaria": "12345",
            "ano_vigente": "2024",
            "sei_numero": "999999",             
            "doc": "DOE",
            "observacoes":"44444",
            "tipo_insubsistencia":"designacao"
        }

        serializer = InsubsistenciaSerializer(data=data)

        assert serializer.is_valid(), serializer.errors


    @pytest.mark.django_db
    def test_serializer_valido_na_designacao_com_cessacao_com_insubsistencia(self):
        designacao = self._criar_designacao()

        cessacao = Cessacao.objects.create(
            designacao=designacao,
            numero_portaria="12345",
            ano_vigente="2024",
            sei_numero="999999",             
            doc="DOE",
            data_designacao="2024-03-10"
        )

        Insubsistencia.objects.create(
            cessacao_id=cessacao.id,
            numero_portaria="12345",
            ano_vigente="2024",
            sei_numero="999999",             
            doc="DOE",
            observacoes="44444",
        )

        data = {
            "designacao": designacao.id,
            "numero_portaria": "12345",
            "ano_vigente": "2024",
            "sei_numero": "999999",             
            "doc": "DOE",
            "observacoes":"44444",
            "tipo_insubsistencia":"designacao"
        }

        serializer = InsubsistenciaSerializer(data=data)

        assert serializer.is_valid(), serializer.errors


    @pytest.mark.django_db
    def test_numero_portaria_invalido(self):
        designacao = self._criar_designacao()

 
        data = {
            "designacao": designacao.id,
            "numero_portaria": "12A45",
            "ano_vigente": "2024",
            "sei_numero": "999999",             
            "doc": "DOE",
            "observacoes":"44444",
            "tipo_insubsistencia":"designacao"
        }

        serializer = InsubsistenciaSerializer(data=data)

        assert not serializer.is_valid()
        assert "numero_portaria" in serializer.errors


    @pytest.mark.django_db
    def test_ano_vigente_invalido(self):
        designacao = self._criar_designacao()

        data = {
            "designacao": designacao.id,
            "numero_portaria": "12A45",
            "ano_vigente": "20A4",
            "sei_numero": "999999",             
            "doc": "DOE",
            "observacoes":"44444",
            "tipo_insubsistencia":"designacao"
        }

        serializer = InsubsistenciaSerializer(data=data)

        assert not serializer.is_valid()
        assert "ano_vigente" in serializer.errors


    @pytest.mark.django_db
    def test_tipo_insubsistencia_invalido(self):
        designacao = self._criar_designacao()

        data = {
            "designacao": designacao.id,
            "numero_portaria": "12A45",
            "ano_vigente": "20A4",
            "sei_numero": "99999",
            "doc": "DOE",
            "observacoes":"44444",
            "tipo_insubsistencia":"invalido"
         }

        serializer = InsubsistenciaSerializer(data=data)
        
        assert not serializer.is_valid()
        assert "tipo_insubsistencia" in serializer.errors
        print("serializer.errors",serializer)


 
    @pytest.mark.django_db
    def test_nao_permite_insubsistencia_duplicada_na_designacao(self):
        designacao = self._criar_designacao()

        # cria primeira insubsistencia
        Insubsistencia.objects.create(
            designacao=designacao,
            numero_portaria="12345",
            ano_vigente="2024",
            sei_numero="999999",             
            doc="DOE",
            observacoes="44444",
        )

        data = {
            "designacao": designacao.id,
            "numero_portaria": "54321",
            "ano_vigente": "2024",
            "sei_numero": "888888",
            "doc": "DOE",
            "observacoes":"44444",
            "tipo_insubsistencia":"designacao"
        }

        serializer = InsubsistenciaSerializer(data=data)

        assert not serializer.is_valid()
        assert "non_field_errors" in serializer.errors


    @pytest.mark.django_db
    def test_nao_permite_insubsistencia_duplicada_na_cessacao(self):
        designacao = self._criar_designacao()

        cessacao = Cessacao.objects.create(           
            designacao=designacao,
            numero_portaria="12345",
            ano_vigente="2024",
            sei_numero="999999",
            a_pedido=True,
            remocao=False,
            aposentadoria=False,
            doc="DOE",
            data_designacao="2024-03-10"        
         )   

        # cria primeira insubsistencia
        Insubsistencia.objects.create(
            cessacao_id=cessacao.id,
            numero_portaria="12345",
            ano_vigente="2024",
            sei_numero="999999",             
            doc="DOE",
            observacoes="44444",
        )

 
        data = {
            "designacao": designacao.id,
            "numero_portaria": "54321",
            "ano_vigente": "2024",
            "sei_numero": "888888",
            "doc": "DOE",
            "observacoes":"44444",
            "tipo_insubsistencia":"cessacao"
        }

        serializer = InsubsistenciaSerializer(data=data)
        
        assert not serializer.is_valid()
        assert "non_field_errors" in serializer.errors



 
    @pytest.mark.django_db
    def test_nao_permite_insubsistencia_sem_cessacao_e_sem_designacao(self):
 
        data = {
            "numero_portaria": "54321",
            "ano_vigente": "2024",
            "sei_numero": "888888",
            "doc": "DOE",
            "observacoes":"44444",
            "tipo_insubsistencia":"cessacao"
        }

        serializer = InsubsistenciaSerializer(data=data)
        
        assert not serializer.is_valid()
        assert "non_field_errors" in serializer.errors

