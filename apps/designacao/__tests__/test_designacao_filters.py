from django.test import TestCase
from apps.designacao.models.designacao import Designacao, ImpedimentoSubstituicao
from apps.designacao.api.filters.designacao_filter import DesignacaoFilter
import datetime


class DesignacaoFilterTest(TestCase):

    def setUp(self):
        self.impedimento1 = ImpedimentoSubstituicao.objects.create(
            codigo='IMP1',
            descricao='Impedimento 1'
        )
        self.impedimento2 = ImpedimentoSubstituicao.objects.create(
            codigo='IMP2',
            descricao='Impedimento 2'
        )

        self.designacao1 = Designacao.objects.create(
            dre_nome='DRE Norte',
            unidade_proponente='EMEF Teste 1',
            codigo_hierarquico='001',
            indicado_nome_civil='João da Silva',
            indicado_nome_servidor='João Silva',
            indicado_rf='1234567',
            indicado_vinculo=1,
            indicado_codigo_cargo_base=1,
            indicado_cargo_sobreposto='Diretor',
            indicado_lotacao='Unidade A',
            indicado_local_exercicio='Unidade A',
            titular_nome_servidor='Maria Souza',
            titular_rf='9999999',
            titular_codigo_cargo_base=1,
            titular_cargo_sobreposto='Vice-Diretor',
            numero_portaria='001',
            ano_vigente='2024',
            sei_numero='SEI-001',
            data_inicio=datetime.date(2024, 1, 1),
            tipo_vaga=Designacao.TipoVaga.VAGO,
            impedimento_substituicao=self.impedimento1,
            cargo_vaga=1,
        )

        self.designacao2 = Designacao.objects.create(
            dre_nome='DRE Sul',
            unidade_proponente='EMEF Teste 2',
            codigo_hierarquico='002',
            indicado_nome_civil='Carlos de Lima',
            indicado_nome_servidor='Carlos Lima',
            indicado_rf='0000000',
            indicado_vinculo=2,
            indicado_codigo_cargo_base=2,
            indicado_cargo_sobreposto='Supervisor',
            indicado_lotacao='Unidade B',
            indicado_local_exercicio='Unidade B',
            titular_nome_servidor='Ana Paula',
            titular_rf='7654321',
            titular_codigo_cargo_base=2,
            titular_cargo_sobreposto='Diretor',
            numero_portaria='002',
            ano_vigente='2024',
            sei_numero='SEI-002',
            data_inicio=datetime.date(2024, 2, 1),
            tipo_vaga=Designacao.TipoVaga.DISPONIVEL,
            impedimento_substituicao=self.impedimento2,
            cargo_vaga=2,
        )

    def test_filter_rf(self):
        f = DesignacaoFilter({'rf': '1234567'}, queryset=Designacao.objects.all())
        self.assertIn(self.designacao1, f.qs)
        self.assertNotIn(self.designacao2, f.qs)

    def test_filter_nome(self):
        f = DesignacaoFilter({'nome': 'Ana'}, queryset=Designacao.objects.all())
        self.assertIn(self.designacao2, f.qs)
        self.assertNotIn(self.designacao1, f.qs)

    def test_filter_cargo_base(self):
        f = DesignacaoFilter({'cargo_base': 1}, queryset=Designacao.objects.all())
        self.assertIn(self.designacao1, f.qs)
        self.assertNotIn(self.designacao2, f.qs)

    def test_filter_cargo_sobreposto(self):
        f = DesignacaoFilter({'cargo_sobreposto': 2}, queryset=Designacao.objects.all())
        self.assertIn(self.designacao2, f.qs)
        self.assertNotIn(self.designacao1, f.qs)

    def test_filter_dre(self):
        f = DesignacaoFilter({'dre': 'Norte'}, queryset=Designacao.objects.all())
        self.assertIn(self.designacao1, f.qs)
        self.assertNotIn(self.designacao2, f.qs)

    def test_filter_unidade(self):
        f = DesignacaoFilter({'unidade': 'Teste 2'}, queryset=Designacao.objects.all())
        self.assertIn(self.designacao2, f.qs)
        self.assertNotIn(self.designacao1, f.qs)

    def test_filter_ano(self):
        f = DesignacaoFilter({'ano': '2024'}, queryset=Designacao.objects.all())
        self.assertEqual(f.qs.count(), 2)

    def test_filter_periodo(self):
        f = DesignacaoFilter({
            'periodo_after': '2024-01-15',
            'periodo_before': '2024-12-31'
        }, queryset=Designacao.objects.all())

        self.assertIn(self.designacao2, f.qs)
        self.assertNotIn(self.designacao1, f.qs)

    def test_filter_impedimento_substituicao(self):
        f = DesignacaoFilter({
            'impedimento_substituicao': self.impedimento1.id
        }, queryset=Designacao.objects.all())

        self.assertIn(self.designacao1, f.qs)
        self.assertNotIn(self.designacao2, f.qs)

    def test_filter_impedimento_codigo(self):
        f = DesignacaoFilter({
            'impedimento_codigo': 'IMP2'
        }, queryset=Designacao.objects.all())

        self.assertIn(self.designacao2, f.qs)
        self.assertNotIn(self.designacao1, f.qs)