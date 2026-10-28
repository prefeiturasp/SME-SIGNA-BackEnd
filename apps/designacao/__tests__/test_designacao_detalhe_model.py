"""Testes do modelo de detalhe de designação."""

import datetime

import pytest
from django.db import IntegrityError, transaction

from apps.designacao.__tests__.factories import criar_ato_designacao
from apps.designacao.models.designacao import ImpedimentoSubstituicao
from apps.designacao.models.designacao_detalhe import DesignacaoDetalhe

pytestmark = pytest.mark.django_db


class TestDesignacaoDetalheEscolhas:
    """Valores fixos de tipo de vaga e códigos legados de cargo."""

    def test_tipo_de_vaga(self):
        assert DesignacaoDetalhe.TipoVaga.VAGO == "VAGO"
        assert DesignacaoDetalhe.TipoVaga.VAGO.label == "Cargo Vago"
        assert DesignacaoDetalhe.TipoVaga.DISPONIVEL == "DISPONIVEL"
        assert (
            DesignacaoDetalhe.TipoVaga.DISPONIVEL.label == "Cargo Disponível"
        )

    def test_codigos_legados_de_cargo(self):
        assert DesignacaoDetalhe.CargoVaga.ASSISTENTE_DIRETOR == 3085
        assert DesignacaoDetalhe.CargoVaga.DIRETOR == 3360
        assert DesignacaoDetalhe.CargoVaga.COORDENADOR_PEDAGOGICO == 3379
        assert DesignacaoDetalhe.CargoVaga.SECRETARIO == 3182
        assert DesignacaoDetalhe.CargoVaga.SUPERVISOR == 3352
        assert DesignacaoDetalhe.CargoVaga.DIRETOR.label == "DIRETOR DE ESCOLA"


class TestDesignacaoDetalhePersistencia:
    """Persistência, chave e relações do detalhe."""

    def test_tabela_e_chave_primaria_sao_o_ato(self):
        ato = criar_ato_designacao()
        detalhe = ato.designacao_detalhe

        assert DesignacaoDetalhe._meta.db_table == "designacao_detalhe"
        assert detalhe.pk == ato.pk
        assert detalhe.ato_id == ato.pk

    def test_valores_padrao(self):
        detalhe = criar_ato_designacao().designacao_detalhe

        assert detalhe.indicado_categoria == ""
        assert detalhe.indicado_codigo_ue_lotacao == ""
        assert detalhe.indicado_possui_cargo_sobreposto is False
        assert detalhe.ue == ""
        assert detalhe.dre == ""
        assert detalhe.funcionarios_da_unidade == ""
        assert detalhe.data_fim is None
        assert detalhe.carater_excepcional is False
        assert detalhe.com_afastamento is False
        assert detalhe.possui_pendencia is False
        assert detalhe.pendencias == ""
        assert detalhe.motivo_afastamento == ""
        assert detalhe.informacoes_adicionais == ""
        assert detalhe.detalhe_para_quadro_de_historico_por_ano is True
        assert detalhe.impedimento_substituicao_id is None
        assert detalhe.cargo_vaga is None

    def test_aceita_codigo_de_cargo_fora_do_enum_legado(self):
        detalhe = criar_ato_designacao(cargo_vaga=99999).designacao_detalhe

        assert detalhe.cargo_vaga == 99999

    def test_um_ato_so_pode_ter_um_detalhe(self):
        ato = criar_ato_designacao()

        with pytest.raises(IntegrityError), transaction.atomic():
            DesignacaoDetalhe.objects.create(
                ato=ato,
                dre_nome="DRE",
                unidade_proponente="Escola",
                codigo_hierarquico="001",
                indicado_nome_servidor="Servidor",
                indicado_rf="1234567",
                indicado_vinculo=1,
                indicado_cargo_base="Cargo",
                indicado_lotacao="Lotação",
                indicado_local_exercicio="Local",
                data_inicio=datetime.date(2024, 1, 1),
                tipo_vaga=DesignacaoDetalhe.TipoVaga.VAGO,
            )

    def test_excluir_o_ato_remove_o_detalhe(self):
        ato = criar_ato_designacao()
        pk = ato.pk

        ato.delete()

        assert not DesignacaoDetalhe.objects.filter(pk=pk).exists()

    def test_excluir_impedimento_zera_a_referencia(self):
        impedimento = ImpedimentoSubstituicao.objects.create(
            codigo="LIC", descricao="Licença"
        )
        ato = criar_ato_designacao(impedimento_substituicao=impedimento)

        impedimento.delete()
        ato.designacao_detalhe.refresh_from_db()

        assert ato.designacao_detalhe.impedimento_substituicao_id is None
