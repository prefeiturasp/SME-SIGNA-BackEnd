"""Testes para serviço de designação."""

import datetime

import pytest
from rest_framework.exceptions import ValidationError

from apps.designacao.__tests__.factories import (
    criar_ato_cessacao,
    criar_ato_designacao,
)
from apps.designacao.models.ato_administrativo import AtoAdministrativo
from apps.designacao.models.designacao_detalhe import DesignacaoDetalhe
from apps.designacao.services.designacao_service import DesignacaoService


@pytest.mark.django_db
class TestDesignacaoService:
    """Testes para designacao service."""

    def test_criar_designacao(self):
        """Verifica criação de designação via service."""
        data = {
            "numero_portaria": 555,
            "ano_vigente": "2024",
            "sei_numero": "SEI-555",
            "dre_nome": "DRE Teste",
            "unidade_proponente": "Escola Teste",
            "codigo_hierarquico": "001",
            "indicado_nome_civil": "Nome Civil",
            "indicado_nome_servidor": "Nome Servidor",
            "indicado_rf": "1234567",
            "indicado_vinculo": 1,
            "indicado_cargo_base": "Cargo Base",
            "indicado_lotacao": "Lotacao",
            "indicado_local_exercicio": "Local",
            "data_inicio": datetime.date(2024, 1, 1),
            "tipo_vaga": DesignacaoDetalhe.TipoVaga.VAGO,
        }

        ato = DesignacaoService.criar(data)

        assert ato.tipo == AtoAdministrativo.Tipo.DESIGNACAO
        assert (
            ato.status_publicacao
            == AtoAdministrativo.StatusPublicacao.NAO_PUBLICADO
        )
        assert ato.numero_portaria == 555
        assert ato.designacao_detalhe.indicado_nome_civil == "Nome Civil"

    def test_excluir_sem_dependentes(self):
        """Verifica exclusão de designação sem atos derivados."""
        designacao = criar_ato_designacao()

        DesignacaoService.excluir(designacao)

        assert not AtoAdministrativo.objects.filter(pk=designacao.pk).exists()

    def test_excluir_com_dependentes_gera_erro(self):
        """Verifica que exclusão é bloqueada quando há atos derivados."""
        designacao = criar_ato_designacao()
        criar_ato_cessacao(designacao)

        with pytest.raises(ValidationError):
            DesignacaoService.excluir(designacao)

        assert AtoAdministrativo.objects.filter(pk=designacao.pk).exists()

    def test_get_cargos_pareados_sucesso(self):
        """Verifica get cargos pareados sucesso."""
        criar_ato_designacao(
            indicado_codigo_cargo_base=1,
            indicado_cargo_base="Professor",
            titular_codigo_cargo_base=2,
            titular_cargo_base="Diretor",
        )
        criar_ato_designacao(
            indicado_codigo_cargo_base=3,
            indicado_cargo_base="Coordenador",
        )

        queryset = AtoAdministrativo.objects.filter(
            tipo=AtoAdministrativo.Tipo.DESIGNACAO
        )

        resultado = DesignacaoService.get_cargos_pareados(
            queryset,
            "designacao_detalhe__indicado_codigo_cargo_base",
            "designacao_detalhe__indicado_cargo_base",
            "designacao_detalhe__titular_codigo_cargo_base",
            "designacao_detalhe__titular_cargo_base",
        )

        assert resultado == [
            {"codigoCargo": 3, "nomeCargo": "Coordenador"},
            {"codigoCargo": 2, "nomeCargo": "Diretor"},
            {"codigoCargo": 1, "nomeCargo": "Professor"},
        ]

    def test_get_cargos_pareados_remove_invalidos(self):
        """Verifica get cargos pareados remove invalidos."""
        criar_ato_designacao(
            indicado_codigo_cargo_base=None,
            indicado_cargo_base="",
            titular_codigo_cargo_base=None,
            titular_cargo_base="",
        )

        queryset = AtoAdministrativo.objects.filter(
            tipo=AtoAdministrativo.Tipo.DESIGNACAO
        )

        resultado = DesignacaoService.get_cargos_pareados(
            queryset,
            "designacao_detalhe__indicado_codigo_cargo_base",
            "designacao_detalhe__indicado_cargo_base",
            "designacao_detalhe__titular_codigo_cargo_base",
            "designacao_detalhe__titular_cargo_base",
        )

        assert resultado == []

    def test_create_designacao(self):
        """Verifica create designação."""
        designacao = criar_ato_designacao()
        assert (
            designacao.status_publicacao
            == AtoAdministrativo.StatusPublicacao.NAO_PUBLICADO
        )

    def test_atualizar_campos_do_ato(self):
        """Verifica atualização de campos pertencentes ao ato."""
        designacao = criar_ato_designacao(numero_portaria=111)

        atualizado = DesignacaoService.atualizar(
            designacao, {"numero_portaria": 999}
        )

        atualizado.refresh_from_db()
        assert atualizado.numero_portaria == 999

    def test_atualizar_campos_do_detalhe(self):
        """Verifica atualização de campos pertencentes ao detalhe."""
        designacao = criar_ato_designacao(indicado_nome_civil="Antigo")

        atualizado = DesignacaoService.atualizar(
            designacao, {"indicado_nome_civil": "Novo Nome"}
        )

        atualizado.designacao_detalhe.refresh_from_db()
        assert atualizado.designacao_detalhe.indicado_nome_civil == "Novo Nome"

    def test_atualizar_campos_do_ato_e_do_detalhe(self):
        """Verifica atualização simultânea de campos do ato e do detalhe."""
        designacao = criar_ato_designacao(
            numero_portaria=111, indicado_nome_civil="Antigo"
        )

        atualizado = DesignacaoService.atualizar(
            designacao,
            {"numero_portaria": 222, "indicado_nome_civil": "Novo Nome"},
        )

        atualizado.refresh_from_db()
        atualizado.designacao_detalhe.refresh_from_db()
        assert atualizado.numero_portaria == 222
        assert atualizado.designacao_detalhe.indicado_nome_civil == "Novo Nome"

    def test_erro_atualizar_texto_sei_quando_ja_publicado(self):
        """Verifica que texto_sei não pode ser reescrito após publicação."""
        designacao = criar_ato_designacao(doc=datetime.date(2024, 5, 1))

        with pytest.raises(ValidationError, match="já publicado"):
            DesignacaoService.atualizar(
                designacao, {"texto_sei": "Texto reescrito"}
            )

    def test_erro_atualizar_modelo_portaria_quando_ja_publicado(self):
        """Verifica que modelo_portaria também fica congelado após publicação."""
        designacao = criar_ato_designacao(doc=datetime.date(2024, 5, 1))

        with pytest.raises(ValidationError, match="já publicado"):
            DesignacaoService.atualizar(designacao, {"modelo_portaria": 1})

    def test_permite_atualizar_texto_sei_quando_nao_publicado(self):
        """Verifica que texto_sei pode ser corrigido antes da publicação."""
        designacao = criar_ato_designacao()
        assert designacao.doc is None

        atualizado = DesignacaoService.atualizar(
            designacao, {"texto_sei": "Texto corrigido"}
        )

        atualizado.refresh_from_db()
        assert atualizado.texto_sei == "Texto corrigido"

    def test_get_cargos_pareados_remove_duplicados(self):
        """Verifica get cargos pareados remove duplicados."""
        criar_ato_designacao(
            indicado_codigo_cargo_base=1,
            indicado_cargo_base="Professor",
            titular_codigo_cargo_base=1,
            titular_cargo_base="Professor",
        )

        queryset = AtoAdministrativo.objects.filter(
            tipo=AtoAdministrativo.Tipo.DESIGNACAO
        )

        resultado = DesignacaoService.get_cargos_pareados(
            queryset,
            "designacao_detalhe__indicado_codigo_cargo_base",
            "designacao_detalhe__indicado_cargo_base",
            "designacao_detalhe__titular_codigo_cargo_base",
            "designacao_detalhe__titular_cargo_base",
        )

        assert resultado == [{"codigoCargo": 1, "nomeCargo": "Professor"}]


def _dados_substituicao_diretor(**kwargs):
    """Monta dados de designação para substituição do Diretor."""
    data = {
        "numero_portaria": 777,
        "ano_vigente": "2024",
        "sei_numero": "SEI-777",
        "dre_nome": "DRE Teste",
        "unidade_proponente": "EMEF Teste",
        "codigo_hierarquico": "001",
        "indicado_nome_civil": "Nome Civil",
        "indicado_nome_servidor": "Nome Servidor",
        "indicado_rf": "1234567",
        "indicado_vinculo": 1,
        "indicado_cargo_base": "PROF.ENS.FUND.II E MED.-CIENCIAS",
        "indicado_codigo_cargo_base": 3255,
        "indicado_lotacao": "EMEF Teste",
        "indicado_codigo_ue_lotacao": "090450",
        "ue": "090450",
        "indicado_local_exercicio": "EMEF Teste",
        "data_inicio": datetime.date(2024, 1, 1),
        "data_fim": datetime.date(2024, 1, 16),
        "tipo_vaga": DesignacaoDetalhe.TipoVaga.DISPONIVEL,
        "cargo_vaga": DesignacaoDetalhe.CargoVaga.DIRETOR,
    }
    data.update(kwargs)
    return data


@pytest.mark.django_db
class TestDesignacaoServiceSubstituicaoDiretor:
    """Testes das regras de substituição do Diretor."""

    @pytest.mark.parametrize(
        "data_fim",
        [datetime.date(2024, 1, 16), datetime.date(2024, 1, 30)],
    )
    def test_permite_periodo_de_16_a_30_dias(self, data_fim):
        """Verifica que 16 a 30 dias é aceito como substituição formal."""
        ato = DesignacaoService.criar(
            _dados_substituicao_diretor(data_fim=data_fim)
        )

        assert ato.designacao_detalhe.data_fim == data_fim

    def test_bloqueia_periodo_menor_que_16_dias(self):
        """Verifica que período inferior a 16 dias é bloqueado."""
        with pytest.raises(ValidationError) as exc:
            DesignacaoService.criar(
                _dados_substituicao_diretor(
                    data_fim=datetime.date(2024, 1, 15)
                )
            )

        assert "16 a 30 dias" in str(exc.value.detail["data_fim"])
        assert exc.value.get_codes() == {"data_fim": ["periodo_insuficiente"]}
        assert not AtoAdministrativo.objects.exists()

    @pytest.mark.parametrize("data_fim", [datetime.date(2024, 1, 31), None])
    def test_bloqueia_periodo_acima_de_30_dias_indicando_eleicao(
        self, data_fim
    ):
        """Verifica que acima de 30 dias (ou sem fim) exige eleição."""
        with pytest.raises(ValidationError) as exc:
            DesignacaoService.criar(
                _dados_substituicao_diretor(data_fim=data_fim)
            )

        assert "eleição" in str(exc.value.detail["data_fim"])
        assert exc.value.get_codes() == {"data_fim": ["eleicao_necessaria"]}
        assert not AtoAdministrativo.objects.exists()

    def test_bloqueia_professor_de_outra_unidade(self):
        """Verifica bloqueio de professor de outra unidade escolar."""
        with pytest.raises(ValidationError) as exc:
            DesignacaoService.criar(
                _dados_substituicao_diretor(
                    indicado_codigo_ue_lotacao="090451"
                )
            )

        assert "mesma unidade escolar" in str(
            exc.value.detail["indicado_codigo_ue_lotacao"]
        )
        assert exc.value.get_codes() == {
            "indicado_codigo_ue_lotacao": ["unidade_diferente"]
        }

    def test_permite_professor_da_mesma_unidade_ignorando_zeros(self):
        """Verifica que a comparação de código ignora zeros à esquerda."""
        ato = DesignacaoService.criar(
            _dados_substituicao_diretor(indicado_codigo_ue_lotacao=90450)
        )

        assert ato.pk is not None

    def test_compara_por_codigo_e_nao_por_nome(self):
        """Verifica que nomes diferentes com o mesmo código são aceitos."""
        ato = DesignacaoService.criar(
            _dados_substituicao_diretor(indicado_lotacao="EMEF - TESTE")
        )

        assert ato.pk is not None

    @pytest.mark.parametrize(
        "campos",
        [{"indicado_codigo_ue_lotacao": ""}, {"ue": ""}],
    )
    def test_bloqueia_professor_sem_codigo_de_unidade(self, campos):
        """Verifica bloqueio quando não é possível comparar as unidades."""
        with pytest.raises(ValidationError) as exc:
            DesignacaoService.criar(_dados_substituicao_diretor(**campos))

        assert exc.value.get_codes() == {
            "indicado_codigo_ue_lotacao": ["unidade_diferente"]
        }

    @pytest.mark.parametrize(
        ("cargo_base", "codigo_cargo_base"),
        [
            ("SECRETARIO DE ESCOLA", 3182),
            ("Profissional Eng, Arq, Agron e Geologia - N I", 2666),
        ],
    )
    def test_bloqueia_nao_professor_mesmo_da_mesma_unidade(
        self, cargo_base, codigo_cargo_base
    ):
        """Verifica que só professor pode substituir o Diretor."""
        with pytest.raises(ValidationError) as exc:
            DesignacaoService.criar(
                _dados_substituicao_diretor(
                    indicado_cargo_base=cargo_base,
                    indicado_codigo_cargo_base=codigo_cargo_base,
                )
            )

        assert "Somente professor" in str(
            exc.value.detail["indicado_codigo_cargo_base"]
        )
        assert exc.value.get_codes() == {
            "indicado_codigo_cargo_base": ["indicado_nao_professor"]
        }
        assert not AtoAdministrativo.objects.exists()

    def test_bloqueia_cargo_sobreposto_nao_professor_com_base_professor(
        self,
    ):
        """Verifica que o sobreposto define o cargo quando informado."""
        with pytest.raises(ValidationError) as exc:
            DesignacaoService.criar(
                _dados_substituicao_diretor(
                    indicado_cargo_sobreposto="COORDENADOR PEDAGOGICO",
                    indicado_codigo_cargo_sobreposto=3379,
                    indicado_possui_cargo_sobreposto=True,
                )
            )

        assert exc.value.get_codes() == {
            "indicado_codigo_cargo_sobreposto": ["indicado_nao_professor"]
        }

    def test_cargo_sobreposto_professor_de_outra_unidade_e_bloqueado(self):
        """Verifica bloqueio quando o sobreposto é de professor."""
        with pytest.raises(ValidationError) as exc:
            DesignacaoService.criar(
                _dados_substituicao_diretor(
                    indicado_cargo_base="AUXILIAR TECNICO-SECRETARIA",
                    indicado_codigo_cargo_base=4907,
                    indicado_cargo_sobreposto="PROF.DE ED.INFANTIL",
                    indicado_codigo_cargo_sobreposto=3875,
                    indicado_possui_cargo_sobreposto=True,
                    indicado_codigo_ue_lotacao="090451",
                )
            )

        assert "mesma unidade escolar" in str(
            exc.value.detail["indicado_codigo_ue_lotacao"]
        )

    def test_funcao_atividade_nao_prevalece_sobre_cargo_base(self):
        """Verifica que função/atividade é ignorada e vale o cargo base."""
        with pytest.raises(ValidationError) as exc:
            DesignacaoService.criar(
                _dados_substituicao_diretor(
                    indicado_cargo_sobreposto="PROF.ORIENT.SALA LEITURA",
                    indicado_codigo_cargo_sobreposto=9999,
                    indicado_possui_cargo_sobreposto=False,
                    indicado_codigo_ue_lotacao="090451",
                )
            )

        assert exc.value.get_codes() == {
            "indicado_codigo_ue_lotacao": ["unidade_diferente"]
        }

    @pytest.mark.parametrize(
        "data_fim",
        [datetime.date(2024, 1, 10), datetime.date(2024, 1, 16)],
    )
    def test_bloqueia_indicado_com_cargo_sobreposto_de_ad(self, data_fim):
        """Verifica que quem possui cargo sobreposto de AD é bloqueado."""
        with pytest.raises(ValidationError) as exc:
            DesignacaoService.criar(
                _dados_substituicao_diretor(
                    indicado_cargo_sobreposto=(
                        "ASSISTENTE DE DIRETOR DE ESCOLA"
                    ),
                    indicado_codigo_cargo_sobreposto=3085,
                    indicado_possui_cargo_sobreposto=True,
                    data_fim=data_fim,
                )
            )

        assert "Assistente de Diretor" in str(
            exc.value.detail["indicado_codigo_cargo_sobreposto"]
        )
        assert exc.value.get_codes() == {
            "indicado_codigo_cargo_sobreposto": ["assistente_diretor"]
        }
        assert not AtoAdministrativo.objects.exists()

    def test_funcao_atividade_com_codigo_de_ad_nao_e_bloqueada(self):
        """Verifica que o bloqueio de AD exige cargo sobreposto."""
        ato = DesignacaoService.criar(
            _dados_substituicao_diretor(
                indicado_codigo_cargo_sobreposto=3085,
                indicado_possui_cargo_sobreposto=False,
            )
        )

        assert ato.pk is not None

    def test_cargo_sobreposto_de_ad_em_outra_vaga_e_permitido(self):
        """Verifica que o bloqueio de AD só vale para vaga de Diretor."""
        ato = DesignacaoService.criar(
            _dados_substituicao_diretor(
                cargo_vaga=DesignacaoDetalhe.CargoVaga.SECRETARIO,
                indicado_codigo_cargo_sobreposto=3085,
                indicado_possui_cargo_sobreposto=True,
            )
        )

        assert ato.pk is not None

    def test_bloqueia_troca_do_indicado_para_ad_na_atualizacao(self):
        """Verifica que atualizar o indicado para um AD é bloqueado."""
        ato = DesignacaoService.criar(_dados_substituicao_diretor())

        with pytest.raises(ValidationError) as exc:
            DesignacaoService.atualizar(
                ato,
                {
                    "indicado_codigo_cargo_sobreposto": 3085,
                    "indicado_possui_cargo_sobreposto": True,
                },
            )

        assert exc.value.get_codes() == {
            "indicado_codigo_cargo_sobreposto": ["assistente_diretor"]
        }
        ato.designacao_detalhe.refresh_from_db()
        assert ato.designacao_detalhe.indicado_codigo_cargo_sobreposto is None

    def test_outros_cargos_nao_sao_afetados(self):
        """Verifica que vagas diferentes de Diretor não têm a regra."""
        ato = DesignacaoService.criar(
            _dados_substituicao_diretor(
                cargo_vaga=DesignacaoDetalhe.CargoVaga.SECRETARIO,
                data_fim=None,
                indicado_codigo_ue_lotacao="090451",
            )
        )

        assert ato.pk is not None

    def test_bloqueia_extensao_acima_de_30_dias(self):
        """Verifica que estender a designação além de 30 dias é bloqueado."""
        ato = DesignacaoService.criar(_dados_substituicao_diretor())

        with pytest.raises(ValidationError) as exc:
            DesignacaoService.atualizar(
                ato, {"data_fim": datetime.date(2024, 2, 15)}
            )

        assert "eleição" in str(exc.value.detail["data_fim"])
        ato.designacao_detalhe.refresh_from_db()
        assert ato.designacao_detalhe.data_fim == datetime.date(2024, 1, 16)

    def test_permite_extensao_dentro_de_30_dias(self):
        """Verifica que estender dentro do limite de 30 dias é aceito."""
        ato = DesignacaoService.criar(_dados_substituicao_diretor())

        DesignacaoService.atualizar(
            ato, {"data_fim": datetime.date(2024, 1, 30)}
        )

        ato.designacao_detalhe.refresh_from_db()
        assert ato.designacao_detalhe.data_fim == datetime.date(2024, 1, 30)

    def test_atualizacao_sem_campos_da_regra_nao_revalida(self):
        """Verifica que atualizar outros campos não aplica a regra."""
        ato = criar_ato_designacao(
            cargo_vaga=DesignacaoDetalhe.CargoVaga.DIRETOR
        )

        DesignacaoService.atualizar(ato, {"informacoes_adicionais": "obs"})

        ato.designacao_detalhe.refresh_from_db()
        assert ato.designacao_detalhe.informacoes_adicionais == "obs"
