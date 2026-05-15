import datetime

from django.test import TestCase

from apps.designacao.__tests__.factories import criar_designacao_legado
from apps.designacao.api.filters.designacao_legado_filter import DesignacaoLegadoFilter
from apps.designacao.models.designacao import Designacao, ImpedimentoSubstituicao


class DesignacaoLegadoFilterTest(TestCase):

    def setUp(self):
        self.impedimento1 = ImpedimentoSubstituicao.objects.create(
            codigo="IMP1", descricao="Impedimento 1"
        )
        self.impedimento2 = ImpedimentoSubstituicao.objects.create(
            codigo="IMP2", descricao="Impedimento 2"
        )

        self.d1 = criar_designacao_legado(
            dre_nome="DRE Norte",
            unidade_proponente="EMEF Teste 1",
            indicado_rf="1234567",
            indicado_codigo_cargo_base=1,
            titular_nome_servidor="Maria Souza",
            titular_rf="9999999",
            titular_codigo_cargo_base=1,
            data_inicio=datetime.date(2024, 1, 1),
            impedimento_substituicao=self.impedimento1,
        )

        self.d2 = criar_designacao_legado(
            dre_nome="DRE Sul",
            unidade_proponente="EMEF Teste 2",
            indicado_rf="0000000",
            indicado_codigo_cargo_base=2,
            titular_nome_servidor="Ana Paula",
            titular_rf="7654321",
            titular_codigo_cargo_base=2,
            data_inicio=datetime.date(2024, 2, 1),
            impedimento_substituicao=self.impedimento2,
        )

    def _qs(self):
        return Designacao.objects.filter(is_deleted=False)

    def test_filter_rf_indicado(self):
        f = DesignacaoLegadoFilter({"rf": "1234567"}, queryset=self._qs())
        self.assertIn(self.d1, f.qs)
        self.assertNotIn(self.d2, f.qs)

    def test_filter_rf_titular(self):
        f = DesignacaoLegadoFilter({"rf": "9999999"}, queryset=self._qs())
        self.assertIn(self.d1, f.qs)
        self.assertNotIn(self.d2, f.qs)

    def test_filter_nome(self):
        f = DesignacaoLegadoFilter({"nome": "Ana"}, queryset=self._qs())
        self.assertIn(self.d2, f.qs)
        self.assertNotIn(self.d1, f.qs)

    def test_filter_cargo_base(self):
        f = DesignacaoLegadoFilter({"cargo_base": 1}, queryset=self._qs())
        self.assertIn(self.d1, f.qs)
        self.assertNotIn(self.d2, f.qs)

    def test_filter_dre(self):
        f = DesignacaoLegadoFilter({"dre": "Norte"}, queryset=self._qs())
        self.assertIn(self.d1, f.qs)
        self.assertNotIn(self.d2, f.qs)

    def test_filter_unidade(self):
        f = DesignacaoLegadoFilter({"unidade": "Teste 2"}, queryset=self._qs())
        self.assertIn(self.d2, f.qs)
        self.assertNotIn(self.d1, f.qs)

    def test_filter_ano(self):
        f = DesignacaoLegadoFilter({"ano": "2024"}, queryset=self._qs())
        self.assertEqual(f.qs.count(), 2)

    def test_filter_periodo(self):
        f = DesignacaoLegadoFilter(
            {"periodo_after": "2024-01-15", "periodo_before": "2024-12-31"},
            queryset=self._qs(),
        )
        self.assertIn(self.d2, f.qs)
        self.assertNotIn(self.d1, f.qs)

    def test_filter_impedimento_substituicao(self):
        f = DesignacaoLegadoFilter(
            {"impedimento_substituicao": self.impedimento1.id}, queryset=self._qs()
        )
        self.assertIn(self.d1, f.qs)
        self.assertNotIn(self.d2, f.qs)

    def test_filter_impedimento_codigo(self):
        f = DesignacaoLegadoFilter({"impedimento_codigo": "IMP2"}, queryset=self._qs())
        self.assertIn(self.d2, f.qs)
        self.assertNotIn(self.d1, f.qs)
