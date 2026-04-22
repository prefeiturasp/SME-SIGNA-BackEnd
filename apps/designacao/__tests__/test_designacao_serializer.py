import pytest
from django.test import TestCase
from apps.designacao.models.designacao import Designacao, ImpedimentoSubstituicao
from apps.designacao.models.insubsistencia import Insubsistencia
from apps.designacao.api.serializers.designacao_serializer import DesignacaoSerializer
from apps.designacao.__tests__.factories import criar_designacao

class DesignacaoSerializerTest(TestCase):
    def test_get_field_names_inclui_campos_extras(self):
        serializer = DesignacaoSerializer()
        fields = serializer.fields

        self.assertIn('impedimento_substituicao_detail', fields)
        self.assertIn('tipo_vaga_display', fields)
        self.assertIn('cargo_vaga_display', fields)


    @pytest.mark.django_db
    def test_get_impedimento_display_com_valor(self):
        impedimento = ImpedimentoSubstituicao.objects.get(codigo='LIC_MEDICA')

        designacao = Designacao.objects.create(
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
            impedimento_substituicao=impedimento
        )

        serializer = DesignacaoSerializer(designacao)

        assert serializer.data['impedimento_display'] == 'Por licença médica'

    @pytest.mark.django_db
    def test_get_impedimento_display_sem_valor(self):
        designacao = Designacao.objects.create(
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
            impedimento_substituicao=None
        )

        serializer = DesignacaoSerializer(designacao)

        assert serializer.data['impedimento_display'] is None

    @pytest.mark.django_db
    def test_update_nao_permite_alterar_campos_protegidos(self):
        designacao = Designacao.objects.create(
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

        serializer = DesignacaoSerializer()

        updated = serializer.update(designacao, {
            "indicado_nome_servidor": "Novo Nome",
            "is_deleted": True,
            "deleted_at": "2025-01-01T00:00:00",
        })

        assert updated.indicado_nome_servidor == "Novo Nome"
        assert updated.is_deleted is False
        assert updated.deleted_at is None


    @pytest.mark.django_db
    def test_get_insubsistencia_retorna_dados_quando_existe_insubsistencia_ativa(self):
        """
        Deve retornar os dados da insubsistência ativa vinculada à designação.
        """
        designacao = criar_designacao()
        insubsistencia = Insubsistencia.objects.create(
            designacao=designacao,
            numero_portaria="11111",
            ano_vigente="2024",
            sei_numero="888888",
        )

        serializer = DesignacaoSerializer(instance=designacao)

        assert serializer.data["insubsistencia"] is not None
        assert serializer.data["insubsistencia"]["id"] == insubsistencia.id

    @pytest.mark.django_db
    def test_update_com_impedimento(self):
        impedimento = ImpedimentoSubstituicao.objects.get(codigo='FERIAS')

        designacao = Designacao.objects.create(
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

        serializer = DesignacaoSerializer()

        updated = serializer.update(designacao, {
            "impedimento_substituicao": impedimento
        })

        assert updated.impedimento_substituicao == impedimento