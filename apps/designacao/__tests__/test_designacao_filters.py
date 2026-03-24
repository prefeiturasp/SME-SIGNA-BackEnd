from django.test import TestCase
from apps.designacao.models.designacao import Designacao
from apps.designacao.api.filters.designacao_filter import DesignacaoFilter
import datetime


class DesignacaoFilterTest(TestCase):

    def setUp(self):
        self.designacao1 = Designacao.objects.create(
            dre_nome='DRE Norte',
            unidade_proponente='EMEF Teste 1',
            codigo_hierarquico='001',
            indicado_nome_civil='João da Silva',
            indicado_nome_servidor='João Silva',
            indicado_rf='1234567',
            indicado_vinculo=1,
            indicado_cargo_base='Professor',
            indicado_lotacao='Unidade A',
            indicado_local_exercicio='Unidade A',
            titular_nome_servidor='Maria Souza',
            titular_rf='9999999',
            numero_portaria='001',
            ano_vigente='2024',
            sei_numero='SEI-001',
            data_inicio=datetime.date(2024, 1, 1),
            tipo_vaga=Designacao.TipoVaga.VAGO,
        )
        self.designacao2 = Designacao.objects.create(
            dre_nome='DRE Sul',
            unidade_proponente='EMEF Teste 2',
            codigo_hierarquico='002',
            indicado_nome_civil='Carlos de Lima',
            indicado_nome_servidor='Carlos Lima',
            indicado_rf='0000000',
            indicado_vinculo=2,
            indicado_cargo_base='Coordenador',
            indicado_lotacao='Unidade B',
            indicado_local_exercicio='Unidade B',
            titular_nome_servidor='Ana Paula',
            titular_rf='7654321',
            numero_portaria='002',
            ano_vigente='2024',
            sei_numero='SEI-002',
            data_inicio=datetime.date(2024, 2, 1),
            tipo_vaga=Designacao.TipoVaga.DISPONIVEL,
        )

    def test_filter_rf_por_indicado(self):
        """Cobre linha 24 - filtra pelo rf do indicado"""
        f = DesignacaoFilter({'rf': '1234567'}, queryset=Designacao.objects.all())
        self.assertIn(self.designacao1, f.qs)
        self.assertNotIn(self.designacao2, f.qs)

    def test_filter_rf_por_titular(self):
        """Cobre linha 24 - filtra pelo rf do titular"""
        f = DesignacaoFilter({'rf': '7654321'}, queryset=Designacao.objects.all())
        self.assertIn(self.designacao2, f.qs)
        self.assertNotIn(self.designacao1, f.qs)

    def test_filter_nome_por_indicado(self):
        """Cobre linha 29 - filtra pelo nome do indicado"""
        f = DesignacaoFilter({'nome': 'João'}, queryset=Designacao.objects.all())
        self.assertIn(self.designacao1, f.qs)
        self.assertNotIn(self.designacao2, f.qs)

    def test_filter_nome_por_titular(self):
        """Cobre linha 29 - filtra pelo nome do titular"""
        f = DesignacaoFilter({'nome': 'Ana'}, queryset=Designacao.objects.all())
        self.assertIn(self.designacao2, f.qs)
        self.assertNotIn(self.designacao1, f.qs)