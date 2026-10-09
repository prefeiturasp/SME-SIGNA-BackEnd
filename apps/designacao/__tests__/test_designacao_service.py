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
from apps.designacao.services.designacao_service import (
    CODIGO_PERIODO_SOBREPOSTO,
    DesignacaoService,
)


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


def _dados_designacao(**kwargs):
    """Monta o payload mínimo de criação de uma substituição."""
    dados = {
        "numero_portaria": 900,
        "ano_vigente": "2024",
        "sei_numero": "SEI-900",
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
        "titular_rf": "7654321",
        "ue": "094765",
        "cargo_vaga": 3360,
        "data_inicio": datetime.date(2024, 2, 1),
        "data_fim": datetime.date(2024, 2, 20),
        "tipo_vaga": DesignacaoDetalhe.TipoVaga.DISPONIVEL,
    }
    dados.update(kwargs)
    return dados


def _criar_existente(**kwargs):
    """Cria substituição existente (UE 094765, Diretor, titular 7654321)."""
    base = {
        "tipo_vaga": DesignacaoDetalhe.TipoVaga.DISPONIVEL,
        "titular_rf": "7654321",
        "ue": "094765",
        "cargo_vaga": 3360,
        "data_inicio": datetime.date(2024, 1, 1),
        "data_fim": datetime.date(2024, 1, 31),
    }
    base.update(kwargs)
    return criar_ato_designacao(**base)


@pytest.mark.django_db
class TestDesignacaoServiceSobreposicao:
    """Testes do bloqueio de sobreposição entre substituições."""

    def test_bloqueia_inicio_no_mesmo_dia_do_termino(self):
        """Início no dia do término da anterior é sobreposição."""
        _criar_existente()

        with pytest.raises(ValidationError) as exc:
            DesignacaoService.criar(
                _dados_designacao(data_inicio=datetime.date(2024, 1, 31))
            )

        mensagem = str(exc.value.detail["data_inicio"][0])
        assert "31/01/2024" in mensagem
        assert "01/02/2024" in mensagem
        assert exc.value.get_codes() == {
            "data_inicio": [CODIGO_PERIODO_SOBREPOSTO]
        }

    def test_permite_inicio_no_dia_seguinte_ao_termino(self):
        """Início no dia seguinte ao término não sobrepõe."""
        _criar_existente()

        ato = DesignacaoService.criar(_dados_designacao())

        assert ato.pk is not None

    def test_bloqueia_sobreposicao_no_meio_do_periodo(self):
        """Período que começa no meio de outra substituição é bloqueado."""
        _criar_existente()

        with pytest.raises(ValidationError):
            DesignacaoService.criar(
                _dados_designacao(data_inicio=datetime.date(2024, 1, 15))
            )

    def test_bloqueia_nova_que_termina_dentro_da_existente(self):
        """Nova substituição anterior que avança sobre a existente."""
        _criar_existente()

        with pytest.raises(ValidationError):
            DesignacaoService.criar(
                _dados_designacao(
                    data_inicio=datetime.date(2023, 12, 1),
                    data_fim=datetime.date(2024, 1, 1),
                )
            )

    def test_permite_nova_que_termina_antes_da_existente(self):
        """Nova substituição inteiramente anterior não sobrepõe."""
        _criar_existente()

        ato = DesignacaoService.criar(
            _dados_designacao(
                data_inicio=datetime.date(2023, 12, 1),
                data_fim=datetime.date(2023, 12, 31),
            )
        )

        assert ato.pk is not None

    def test_bloqueia_existente_sem_data_final(self):
        """Substituição existente sem data final vale em aberto."""
        _criar_existente(data_fim=None)

        with pytest.raises(ValidationError) as exc:
            DesignacaoService.criar(
                _dados_designacao(data_inicio=datetime.date(2025, 1, 1))
            )

        assert "sem data final" in str(exc.value.detail["data_inicio"][0])

    def test_bloqueia_nova_sem_data_final(self):
        """Nova substituição sem data final sobrepõe as posteriores."""
        _criar_existente(
            data_inicio=datetime.date(2024, 6, 1),
            data_fim=datetime.date(2024, 6, 30),
        )

        with pytest.raises(ValidationError):
            DesignacaoService.criar(_dados_designacao(data_fim=None))

    def test_usa_data_da_cessacao_ativa_como_termino(self):
        """Com cessação ativa, a substituição termina na data da cessação."""
        existente = _criar_existente(data_fim=None)
        criar_ato_cessacao(existente, data_cessacao=datetime.date(2024, 1, 31))

        DesignacaoService.criar(_dados_designacao())

        with pytest.raises(ValidationError):
            DesignacaoService.criar(
                _dados_designacao(data_inicio=datetime.date(2024, 1, 31))
            )

    def test_ignora_cessacao_inativa(self):
        """Cessação tornada insubsistente não encerra a substituição."""
        existente = _criar_existente(data_fim=None)
        cessacao = criar_ato_cessacao(
            existente, data_cessacao=datetime.date(2024, 1, 31)
        )
        cessacao.ativo = False
        cessacao.save(update_fields=["ativo"])

        with pytest.raises(ValidationError):
            DesignacaoService.criar(_dados_designacao())

    def test_ignora_designacao_insubsistente(self):
        """Substituição inativa (insubsistente) não é considerada."""
        existente = _criar_existente()
        existente.ativo = False
        existente.save(update_fields=["ativo"])

        ato = DesignacaoService.criar(
            _dados_designacao(data_inicio=datetime.date(2024, 1, 15))
        )

        assert ato.pk is not None

    @pytest.mark.parametrize(
        "campo, valor",
        [
            ("ue", "000191"),
            ("cargo_vaga", 3085),
            ("titular_rf", "1111111"),
            ("tipo_vaga", DesignacaoDetalhe.TipoVaga.VAGO),
        ],
    )
    def test_ignora_outra_unidade_cargo_titular_ou_cargo_vago(
        self, campo, valor
    ):
        """Só substituições do mesmo titular, cargo e unidade conflitam."""
        _criar_existente(**{campo: valor})

        ato = DesignacaoService.criar(
            _dados_designacao(data_inicio=datetime.date(2024, 1, 15))
        )

        assert ato.pk is not None

    @pytest.mark.parametrize(
        "campo, valor",
        [
            ("ue", ""),
            ("cargo_vaga", None),
            ("titular_rf", ""),
            ("tipo_vaga", DesignacaoDetalhe.TipoVaga.VAGO),
        ],
    )
    def test_nao_valida_cargo_vago_ou_sem_identificacao(self, campo, valor):
        """Cargo vago ou sem unidade/cargo/titular não é validado."""
        _criar_existente(**{campo: valor})

        ato = DesignacaoService.criar(
            _dados_designacao(
                data_inicio=datetime.date(2024, 1, 15), **{campo: valor}
            )
        )

        assert ato.pk is not None

    def test_edicao_desconsidera_a_propria_designacao(self):
        """Editar o período da própria substituição não conflita com ela."""
        designacao = _criar_existente()

        DesignacaoService.atualizar(
            designacao, {"data_fim": datetime.date(2024, 2, 15)}
        )

        designacao.designacao_detalhe.refresh_from_db()
        assert designacao.designacao_detalhe.data_fim == datetime.date(
            2024, 2, 15
        )

    def test_edicao_bloqueia_ao_estender_sobre_outra(self):
        """Estender o período até a próxima substituição é bloqueado."""
        designacao = _criar_existente()
        _criar_existente(
            data_inicio=datetime.date(2024, 2, 1),
            data_fim=datetime.date(2024, 2, 28),
        )

        with pytest.raises(ValidationError):
            DesignacaoService.atualizar(
                designacao, {"data_fim": datetime.date(2024, 2, 1)}
            )

    def test_edicao_bloqueia_ao_trocar_para_titular_em_conflito(self):
        """Trocar o titular para um já substituído no período bloqueia."""
        designacao = _criar_existente(titular_rf="1111111")
        _criar_existente(
            data_inicio=datetime.date(2024, 1, 10),
            data_fim=datetime.date(2024, 1, 20),
        )

        with pytest.raises(ValidationError):
            DesignacaoService.atualizar(designacao, {"titular_rf": "7654321"})

    def test_edicao_sem_campos_de_periodo_nao_valida(self):
        """Edição que não mexe na substituição nem no período não valida."""
        designacao = _criar_existente()
        _criar_existente()

        DesignacaoService.atualizar(designacao, {"pendencias": "Nova"})

        designacao.designacao_detalhe.refresh_from_db()
        assert designacao.designacao_detalhe.pendencias == "Nova"
