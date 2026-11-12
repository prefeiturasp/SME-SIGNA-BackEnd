"""Testes do serviço de geração da lauda de publicação no D.O.

Cobre a seleção/validação/ordenação dos atos, o texto de publicação
montado para cada tipo de ato (reproduzindo os exemplos da área) e a
geração do arquivo em cada formato.
"""

import datetime

import pytest
from rest_framework.exceptions import ValidationError

from apps.designacao.__tests__.factories import (
    criar_ato_apostila,
    criar_ato_cessacao,
    criar_ato_designacao,
    criar_ato_insubsistencia,
)
from apps.designacao.models.designacao import ImpedimentoSubstituicao
from apps.designacao.models.designacao_detalhe import DesignacaoDetalhe
from apps.designacao.services.lauda_renderers import (
    CONTENT_TYPE_DOCX,
    CONTENT_TYPE_PDF,
    Trecho,
)
from apps.designacao.services.lauda_service import (
    FormatoLauda,
    LaudaService,
)
from apps.gestao.models.cargo_base import CargoBase

# ─── Fixtures ─────────────────────────────────────────────────────────────────

_INDICADO = {
    "dre_nome": "DRE FREGUESIA/BRASILANDIA",
    "indicado_nome_servidor": "ROSELI DE BRITO CABRAL",
    "indicado_nome_civil": "",
    "indicado_rf": "7255667",
    "indicado_vinculo": 2,
    "indicado_cargo_base": "Professor de Ensino Fundamental II e Médio",
    "indicado_codigo_cargo_base": 3255,
    "indicado_categoria": "3",
    "indicado_lotacao": "EMEF Professor Jorge Americano",
    "indicado_codigo_ue_lotacao": "091111",
    "unidade_proponente": "CEI Jardim Primavera I",
    "ue": "400710",
    "codigo_hierarquico": "162400000710000",
    "cargo_vaga": 3360,
    "data_inicio": datetime.date(2026, 2, 5),
}
_TITULAR = {
    "titular_nome_servidor": "ISIS OSTI DE MEDEIROS",
    "titular_rf": "7453361",
    "titular_vinculo": 3,
    "titular_cargo_sobreposto": "Diretor de Escola",
}
_SEI = "6016.2026/0091496-0"
_PROVIMENTO = (
    "portando diploma de Pedagogia e experiência de 3 anos no Magistério"
)


@pytest.fixture(autouse=True)
def cargo_diretor(db):
    CargoBase.objects.update_or_create(
        codigo_cargo="3360",
        defaults={
            # Descrições diferentes de propósito: a lauda usa a completa.
            "descricao_completa": "Diretor de Escola",
            "descricao_resumida": "DE",
            "provimento": _PROVIMENTO,
            "grupamento": CargoBase.Grupamento.GESTORES_EDUCACAO,
            "situacao_funcional": CargoBase.SituacaoFuncional.EFETIVO,
        },
    )


def _designacao(**kwargs):
    dados = {
        "numero_portaria": 88000,
        "ano_vigente": "2026",
        "sei_numero": _SEI,
        "doc": datetime.date(2026, 10, 26),
        **_INDICADO,
    }
    dados.update(kwargs)
    return criar_ato_designacao(**dados)


@pytest.fixture
def designacao_vaga(db):
    return _designacao()


@pytest.fixture
def designacao_substituicao(db):
    return _designacao(**_TITULAR)


def _secao(ato):
    (atual,) = LaudaService.buscar_atos([ato.pk])
    return LaudaService.montar_documento([atual]).secoes[0]


def _corpo(ato) -> str:
    return "".join(trecho.texto for trecho in _secao(ato).corpo)


def _negritos(ato) -> list[str]:
    return [t.texto for t in _secao(ato).corpo if t.negrito]


def _detail(exc) -> str:
    return str(exc.value.detail["detail"])


# ─── buscar_atos ──────────────────────────────────────────────────────────────


class TestBuscarAtos:
    """Seleção, validação e ordenação dos atos que compõem a lauda."""

    def test_erro_id_inexistente(self, designacao_vaga):
        with pytest.raises(ValidationError) as exc:
            LaudaService.buscar_atos([designacao_vaga.pk, 99999])
        assert _detail(exc) == "Atos não encontrados: 99999."
        assert set(exc.value.detail) == {"detail"}

    def test_ordena_por_dre_tipo_e_numero(self, db):
        butanta_10 = _designacao(numero_portaria=10, dre_nome="DRE BUTANTA")
        butanta_5 = _designacao(numero_portaria=5, dre_nome="DRE BUTANTA")
        cessacao = criar_ato_cessacao(butanta_10, numero_portaria=1)
        apostila = criar_ato_apostila(butanta_10, numero_portaria=None)
        campo_limpo = _designacao(
            numero_portaria=1, dre_nome="DRE CAMPO LIMPO"
        )

        ids = [campo_limpo, apostila, cessacao, butanta_10, butanta_5]
        atos = LaudaService.buscar_atos([a.pk for a in ids])

        assert [a.pk for a in atos] == [
            butanta_5.pk,
            butanta_10.pk,
            cessacao.pk,
            apostila.pk,
            campo_limpo.pk,
        ]

    def test_ato_publicado_entra_na_lauda(self, designacao_vaga):
        assert LaudaService.buscar_atos([designacao_vaga.pk]) == [
            designacao_vaga
        ]


# ─── textos por tipo de ato ───────────────────────────────────────────────────


class TestDesignacao:
    """DESIGNANDO / SUBSTITUIÇÃO."""

    def test_cargo_vago(self, designacao_vaga):
        secao = _secao(designacao_vaga)
        assert secao.titulo == "DESIGNANDO"
        assert (
            secao.dre == "Diretoria Regional de Educação FREGUESIA/BRASILANDIA"
        )
        assert _corpo(designacao_vaga) == (
            f"Port. 88000/2026 - SEI nº {_SEI} - 725.566.7, Vínculo 2 - "
            "ROSELI DE BRITO CABRAL, Professor de Ensino Fundamental II e "
            "Médio - Categoria 3, efetivo, lotado(a) na EMEF Professor Jorge "
            "Americano, para exercer o cargo de Diretor de Escola, no CEI "
            "Jardim Primavera I, EH: 162400000710000, cargo vago, previsto "
            "na Lei 14.660/2007, a partir de 05/02/2026, "
            f"{_PROVIMENTO}."
        )

    def test_negrito_no_cabecalho_e_no_nome(self, designacao_vaga):
        assert _negritos(designacao_vaga) == [
            f"Port. 88000/2026 - SEI nº {_SEI} -",
            "ROSELI DE BRITO CABRAL",
        ]

    def test_provimento_vazio_omite_o_trecho(self, designacao_vaga):
        CargoBase.objects.filter(codigo_cargo="3360").update(provimento="")
        assert _corpo(designacao_vaga).endswith(
            "previsto na Lei 14.660/2007, a partir de 05/02/2026."
        )

    def test_provimento_com_ponto_final_nao_duplica(self, designacao_vaga):
        CargoBase.objects.filter(codigo_cargo="3360").update(
            provimento=f"{_PROVIMENTO}. "
        )
        assert _corpo(designacao_vaga).endswith(f", {_PROVIMENTO}.")

    def test_provimento_vem_do_cargo_da_designacao(self, db):
        CargoBase.objects.update_or_create(
            codigo_cargo="3085",
            defaults={
                "descricao_completa": "ASSISTENTE",
                "descricao_eol": "ASSISTENTE",
                "descricao_resumida": "Assistente",
                "provimento": "provimento do assistente",
                "grupamento": CargoBase.Grupamento.GESTORES_EDUCACAO,
                "situacao_funcional": CargoBase.SituacaoFuncional.EFETIVO,
            },
        )
        ato = _designacao(cargo_vaga=3085)
        assert _corpo(ato).endswith(", provimento do assistente.")

    def test_cargo_usa_descricao_completa_e_nao_a_resumida(self, db):
        CargoBase.objects.update_or_create(
            codigo_cargo="3379",
            defaults={
                "descricao_completa": "Coordenador Pedagógico",
                "descricao_eol": "COORDENADOR PEDAGOGICO",
                "descricao_resumida": "CP",
                "grupamento": CargoBase.Grupamento.GESTORES_EDUCACAO,
                "situacao_funcional": CargoBase.SituacaoFuncional.EFETIVO,
            },
        )
        corpo = _corpo(_designacao(cargo_vaga=3379))
        assert "para exercer o cargo de Coordenador Pedagógico, " in corpo
        assert "cargo de CP" not in corpo

    def test_em_substituicao_sem_impedimento(self, designacao_substituicao):
        assert _secao(designacao_substituicao).titulo == "DESIGNANDO"
        assert (
            "EH: 162400000710000, em substituição a ISIS OSTI DE MEDEIROS, "
            "Registro nº 745.336.1, Vínculo 3, Diretor de Escola, efetivo, "
            "a partir de 05/02/2026, "
        ) in _corpo(designacao_substituicao)

    def test_substituicao_por_impedimento_na_referida_unidade(self, db):
        ferias, _ = ImpedimentoSubstituicao.objects.get_or_create(
            codigo="FERIAS", defaults={"descricao": "Por férias"}
        )
        ato = _designacao(
            **_TITULAR,
            indicado_lotacao="CEU EMEI Cantos do Amanhecer",
            indicado_codigo_ue_lotacao="400710",
            impedimento_substituicao=ferias,
            data_inicio=datetime.date(2026, 10, 13),
            data_fim=datetime.date(2026, 11, 1),
        )
        corpo = _corpo(ato)
        assert _secao(ato).titulo == "SUBSTITUIÇÃO"
        assert "lotado(a) no CEU EMEI Cantos do Amanhecer" in corpo
        assert "Diretor de Escola, na referida Unidade, EH:" in corpo
        assert (
            "efetivo, por férias, no período de 13/10/2026 a 01/11/2026, "
        ) in corpo

    def test_nome_civil_tem_prioridade(self, db):
        ato = _designacao(
            indicado_nome_civil="NOME CIVIL",
            titular_nome_servidor="TITULAR SERVIDOR",
            titular_nome_civil="TITULAR CIVIL",
        )
        corpo = _corpo(ato)
        assert "NOME CIVIL" in corpo
        assert "ROSELI" not in corpo
        assert "em substituição a TITULAR CIVIL" in corpo

    def test_cargo_disponivel_e_sem_categoria(self, db):
        ato = _designacao(
            tipo_vaga=DesignacaoDetalhe.TipoVaga.DISPONIVEL,
            indicado_categoria="",
        )
        corpo = _corpo(ato)
        assert "cargo disponível, previsto na Lei" in corpo
        assert "Categoria" not in corpo

    def test_referida_unidade_ignora_zeros_a_esquerda(self, db):
        ato = _designacao(indicado_codigo_ue_lotacao="90450", ue="090450")
        assert "Diretor de Escola, na referida Unidade, EH:" in _corpo(ato)

    def test_unidades_diferentes_nao_usam_referida_unidade(
        self, designacao_vaga
    ):
        corpo = _corpo(designacao_vaga)
        assert "na referida Unidade" not in corpo
        assert "no CEI Jardim Primavera I, EH:" in corpo

    def test_sobreposto_na_unidade_e_cargo_base_em_outra_imprime_nome(
        self, db
    ):
        ato = _designacao(
            indicado_possui_cargo_sobreposto=True,
            indicado_cargo_sobreposto="Coordenador Pedagógico",
            indicado_codigo_ue_lotacao="400710",
            indicado_codigo_ue_cargo_base="091111",
        )
        corpo = _corpo(ato)
        assert "na referida Unidade" not in corpo
        assert "no CEI Jardim Primavera I, EH:" in corpo

    def test_cargo_base_na_unidade_com_sobreposto_em_outra_usa_referida(
        self, db
    ):
        ato = _designacao(
            indicado_possui_cargo_sobreposto=True,
            indicado_cargo_sobreposto="Coordenador Pedagógico",
            indicado_codigo_ue_lotacao="091111",
            indicado_codigo_ue_cargo_base="400710",
        )
        assert "Diretor de Escola, na referida Unidade, EH:" in _corpo(ato)

    def test_ue_do_cargo_base_ignora_zeros_a_esquerda(self, db):
        ato = _designacao(indicado_codigo_ue_cargo_base="90450", ue="090450")
        assert "Diretor de Escola, na referida Unidade, EH:" in _corpo(ato)

    def test_designacao_antiga_sem_sobreposto_usa_lotacao(self, db):
        ato = _designacao(
            indicado_codigo_ue_cargo_base="",
            indicado_possui_cargo_sobreposto=False,
            indicado_codigo_ue_lotacao="400710",
        )
        assert "Diretor de Escola, na referida Unidade, EH:" in _corpo(ato)

    def test_designacao_antiga_com_sobreposto_imprime_nome(self, db):
        ato = _designacao(
            indicado_codigo_ue_cargo_base="",
            indicado_possui_cargo_sobreposto=True,
            indicado_cargo_sobreposto="Coordenador Pedagógico",
            indicado_codigo_ue_lotacao="400710",
        )
        corpo = _corpo(ato)
        assert "na referida Unidade" not in corpo
        assert "no CEI Jardim Primavera I, EH:" in corpo

    def test_cargo_base_nao_professor_sem_categoria(self, db):
        ato = _designacao(indicado_codigo_cargo_base=3360)
        assert "Categoria" not in _corpo(ato)

    def test_cargo_base_do_indicado_vem_do_cadastro_com_categoria(self, db):
        CargoBase.objects.update_or_create(
            codigo_cargo="3875",
            defaults={
                "descricao_completa": "Professor de Educação Infantil",
                "descricao_eol": "PROF.DE ED.INFANTIL",
                "descricao_resumida": "Prof Ed Inf",
                "grupamento": CargoBase.Grupamento.DOCENTES,
                "situacao_funcional": CargoBase.SituacaoFuncional.EFETIVO,
            },
        )
        ato = _designacao(
            indicado_cargo_base="PROF.DE ED.INFANTIL",
            indicado_codigo_cargo_base=3875,
        )
        corpo = _corpo(ato)
        assert (
            "ROSELI DE BRITO CABRAL, Professor de Educação Infantil - "
            "Categoria 3, efetivo"
        ) in corpo
        assert "PROF.DE ED.INFANTIL" not in corpo

    def test_cargo_sobreposto_do_indicado_vem_do_cadastro(self, db):
        ato = _designacao(
            indicado_possui_cargo_sobreposto=True,
            indicado_cargo_sobreposto="DIRETOR DE ESCOLA",
            indicado_codigo_cargo_sobreposto=3360,
        )
        corpo = _corpo(ato)
        assert "ROSELI DE BRITO CABRAL, Diretor de Escola, efetivo" in corpo
        assert "Categoria" not in corpo

    def test_cargo_do_indicado_sem_cadastro_usa_nome_do_eol(self, db):
        ato = _designacao(
            indicado_cargo_base="CARGO SEM CADASTRO",
            indicado_codigo_cargo_base=99999,
        )
        assert "ROSELI DE BRITO CABRAL, CARGO SEM CADASTRO, efetivo" in _corpo(
            ato
        )

    def test_sobreposto_do_indicado_sem_codigo_usa_nome_do_eol(self, db):
        ato = _designacao(
            indicado_possui_cargo_sobreposto=True,
            indicado_cargo_sobreposto="SOBREPOSTO DO EOL",
            indicado_codigo_cargo_sobreposto=None,
        )
        assert "ROSELI DE BRITO CABRAL, SOBREPOSTO DO EOL, efetivo" in _corpo(
            ato
        )

    def test_disponivel_sem_cargo_vaga_usa_cargo_do_titular(self, db):
        ato = _designacao(
            tipo_vaga=DesignacaoDetalhe.TipoVaga.DISPONIVEL,
            cargo_vaga=None,
            titular_nome_servidor="GABRIELA RODRIGUES",
            titular_cargo_base="DIRETOR DE ESCOLA",
            titular_codigo_cargo_base=3360,
        )
        corpo = _corpo(ato)
        assert "para exercer o cargo de Diretor de Escola, " in corpo
        assert corpo.endswith(f", {_PROVIMENTO}.")

    def test_disponivel_sem_cargo_vaga_e_sem_cadastro_usa_nome_do_eol(
        self, db
    ):
        ato = _designacao(
            tipo_vaga=DesignacaoDetalhe.TipoVaga.DISPONIVEL,
            cargo_vaga=None,
            titular_nome_servidor="TITULAR",
            titular_cargo_base="CARGO SEM CADASTRO",
            titular_codigo_cargo_base=99999,
        )
        assert "para exercer o cargo de CARGO SEM CADASTRO, " in _corpo(ato)

    def test_cargo_do_titular_vem_do_cadastro(self, db):
        ato = _designacao(
            titular_nome_servidor="GABRIELA RODRIGUES",
            titular_cargo_base="DIRETOR DE ESCOLA",
            titular_codigo_cargo_base=3360,
        )
        corpo = _corpo(ato)
        assert ", Diretor de Escola, efetivo, a partir de" in corpo
        assert "DIRETOR DE ESCOLA" not in corpo

    def test_cargo_sobreposto_do_titular_vem_do_cadastro(self, db):
        ato = _designacao(
            titular_nome_servidor="TITULAR",
            titular_cargo_base="PROF.DE ED.INFANTIL",
            titular_codigo_cargo_base=3875,
            titular_cargo_sobreposto="DIRETOR DE ESCOLA",
            titular_codigo_cargo_sobreposto=3360,
        )
        corpo = _corpo(ato)
        assert ", Diretor de Escola, efetivo, a partir de" in corpo
        assert "PROF.DE ED.INFANTIL" not in corpo

    def test_cargo_do_titular_sem_cadastro_usa_nome_do_eol(self, db):
        ato = _designacao(
            titular_nome_servidor="TITULAR",
            titular_cargo_base="CARGO SEM CADASTRO",
            titular_codigo_cargo_base=99999,
        )
        assert ", CARGO SEM CADASTRO, efetivo, a partir de" in _corpo(ato)

    def test_sem_codigo_de_ue_compara_nome_da_unidade(self, db):
        ato = _designacao(
            indicado_codigo_ue_lotacao="",
            indicado_codigo_ue_cargo_base="",
            indicado_lotacao="CEI DIRET    - MARIA MARGARIDA, PROFA",
            unidade_proponente="cei diret - maria margarida, profa",
        )
        corpo = _corpo(ato)
        assert "lotado(a) no CEI DIRET - MARIA MARGARIDA, PROFA," in corpo
        assert "Diretor de Escola, na referida Unidade, EH:" in corpo

    def test_sem_codigo_de_ue_e_nomes_diferentes_imprime_nome(self, db):
        ato = _designacao(
            indicado_codigo_ue_lotacao="",
            indicado_codigo_ue_cargo_base="",
        )
        corpo = _corpo(ato)
        assert "na referida Unidade" not in corpo
        assert "no CEI Jardim Primavera I, EH:" in corpo

    def test_com_codigo_de_ue_nao_compara_nome(self, db):
        ato = _designacao(
            indicado_possui_cargo_sobreposto=True,
            indicado_codigo_ue_lotacao="400710",
            indicado_codigo_ue_cargo_base="",
            indicado_lotacao="CEI Jardim Primavera I",
        )
        assert "na referida Unidade" not in _corpo(ato)

    def test_sem_lotacao_nao_usa_referida_unidade(self, db):
        ato = _designacao(
            indicado_codigo_ue_lotacao="",
            indicado_lotacao="",
            unidade_proponente="",
        )
        assert "na referida Unidade" not in _corpo(ato)

    def test_cargo_base_professor_com_categoria(self, db):
        ato = _designacao()
        assert (
            ", Professor de Ensino Fundamental II e Médio - Categoria 3, "
            "efetivo"
        ) in _corpo(ato)

    def test_cargo_sobreposto_substitui_base_sem_categoria(self, db):
        ato = _designacao(
            indicado_possui_cargo_sobreposto=True,
            indicado_cargo_sobreposto="Diretor de Escola",
            indicado_codigo_cargo_sobreposto=3360,
        )
        corpo = _corpo(ato)
        assert "ROSELI DE BRITO CABRAL, Diretor de Escola, efetivo" in corpo
        assert "Professor de Ensino Fundamental II" not in corpo
        assert "Categoria" not in corpo

    def test_cargo_sobreposto_professor_sem_categoria(self, db):
        ato = _designacao(
            indicado_cargo_base="Auxiliar Técnico de Educação",
            indicado_codigo_cargo_base=4906,
            indicado_possui_cargo_sobreposto=True,
            indicado_cargo_sobreposto="Professor de Educação Infantil",
            indicado_codigo_cargo_sobreposto=3875,
        )
        corpo = _corpo(ato)
        assert ", Professor de Educação Infantil, efetivo" in corpo
        assert "Auxiliar Técnico" not in corpo
        assert "Categoria" not in corpo

    def test_sobreposto_sem_nome_usa_cargo_base(self, db):
        ato = _designacao(
            indicado_possui_cargo_sobreposto=True,
            indicado_cargo_sobreposto="  ",
            indicado_codigo_cargo_sobreposto=3360,
        )
        assert " - Categoria 3, efetivo" in _corpo(ato)

    def test_funcao_atividade_nao_substitui_cargo_base(self, db):
        ato = _designacao(
            indicado_possui_cargo_sobreposto=False,
            indicado_cargo_sobreposto="Docência",
            indicado_codigo_cargo_sobreposto=3360,
        )
        corpo = _corpo(ato)
        assert "Docência" not in corpo
        assert (
            ", Professor de Ensino Fundamental II e Médio - Categoria 3, "
            "efetivo"
        ) in corpo

    def test_cargo_base_sem_codigo_sem_categoria(self, db):
        ato = _designacao(indicado_codigo_cargo_base=None)
        assert "Categoria" not in _corpo(ato)

    def test_dre_com_nome_completo_do_eol(self, db):
        ato = _designacao(dre_nome="DIRETORIA REGIONAL DE EDUCACAO BUTANTA")
        assert _secao(ato).dre == "Diretoria Regional de Educação BUTANTA"

    def test_portaria_sem_ano_mostra_so_o_numero(self, db):
        ato = _designacao(ano_vigente="")
        assert _corpo(ato).startswith(f"Port. 88000 - SEI nº {_SEI} - ")


class TestApostila:
    """APOSTILANDO."""

    def test_texto(self, designacao_vaga):
        apostila = criar_ato_apostila(
            designacao_vaga,
            observacao=(
                "que a servidora foi designada para exercer o cargo de "
                "Diretor de Escola a partir de 06/02/2026 e não como constou"
            ),
            sei_numero=_SEI,
            doc=datetime.date(2026, 10, 27),
        )
        secao = _secao(apostila)
        assert secao.titulo == "APOSTILANDO"
        assert _corpo(apostila) == (
            "a portaria nº 88000/2026, de S.M.E., D.O.C. de 26/10/2026, "
            f"SEI nº {_SEI}, em nome de ROSELI DE BRITO CABRAL, registro nº "
            "725.566.7, vínculo 2, a fim de declarar que a servidora foi "
            "designada para exercer o cargo de Diretor de Escola a partir de "
            f"06/02/2026 e não como constou - (SEI nº {_SEI})."
        )

    def test_nao_repete_a_fim_de_declarar(self, designacao_vaga):
        apostila = criar_ato_apostila(
            designacao_vaga, observacao="A fim de declarar que X."
        )
        assert "a fim de declarar que X - (SEI" in _corpo(apostila)

    def test_ato_pai_sem_doc(self, db):
        apostila = criar_ato_apostila(_designacao(doc=None))
        assert "D.O.C. de __/__/____" in _corpo(apostila)


class TestTornarSemEfeito:
    """Insubsistência de apostila."""

    def test_texto(self, designacao_vaga):
        apostila = criar_ato_apostila(
            designacao_vaga, doc=datetime.date(2026, 10, 27)
        )
        insub = criar_ato_insubsistencia(
            apostila,
            numero_portaria=89000,
            ano_vigente="2026",
            sei_numero=_SEI,
        )
        assert _secao(insub).titulo == "TORNAR SEM EFEITO"
        assert _corpo(insub) == (
            f"Port. 89000/2026 - SEI nº {_SEI} - a Apostila feita na "
            "Portaria nº 88000/2026, de S.M.E., D.O.C. de 26/10/2026, em "
            "nome de ROSELI DE BRITO CABRAL, registro nº 725.566.7, "
            "vínculo 2, publicada no D.O.C. de 27/10/2026."
        )


class TestCessacao:
    """FAZENDO CESSAR."""

    def test_cargo_vago_a_pedido(self, designacao_vaga):
        cessacao = criar_ato_cessacao(
            designacao_vaga,
            numero_portaria=89000,
            ano_vigente="2026",
            sei_numero=_SEI,
            a_pedido=True,
            data_cessacao=datetime.date(2026, 10, 21),
        )
        assert _secao(cessacao).titulo == "FAZENDO CESSAR"
        assert _corpo(cessacao) == (
            f"Port. 89000/2026 - SEI nº {_SEI} - 725.566.7, Vínculo 2 - "
            "ROSELI DE BRITO CABRAL, Professor de Ensino Fundamental II e "
            "Médio - Categoria 3, a pedido, os efeitos da Portaria nº 88000, "
            f"de S.M.E., D.O.C. de 26/10/2026, SEI nº {_SEI}, pela qual "
            "o(a) servidor(a) foi designado(a) para exercer o cargo de "
            "Diretor de Escola, no CEI Jardim Primavera I, a partir de "
            "21/10/2026."
        )

    def test_substituicao_sem_motivo(self, designacao_substituicao):
        cessacao = criar_ato_cessacao(
            designacao_substituicao,
            data_cessacao=datetime.date(2026, 10, 20),
        )
        assert (
            "Categoria 3, os efeitos da Portaria nº 88000, de S.M.E., "
        ) in _corpo(cessacao)
        assert (
            "foi designado(a) para substituir o(a) Sr.(a) ISIS OSTI DE "
            "MEDEIROS, Diretor de Escola, registro nº 745.336.1, vínculo 3, "
            "no CEI Jardim Primavera I, a partir de 20/10/2026."
        ) in _corpo(cessacao)


class TestTornandoInsubsistente:
    """Insubsistência de designação, cessação e insubsistência."""

    def test_de_cessacao_em_substituicao(self, designacao_substituicao):
        cessacao = criar_ato_cessacao(
            designacao_substituicao,
            numero_portaria=89000,
            sei_numero=_SEI,
            doc=datetime.date(2026, 10, 30),
        )
        insub = criar_ato_insubsistencia(
            cessacao,
            numero_portaria=90000,
            ano_vigente="2026",
            sei_numero=_SEI,
        )
        assert _secao(insub).titulo == "TORNANDO INSUBSISTENTE"
        assert _corpo(insub) == (
            f"Port. 90000/2026 - SEI nº {_SEI} - 725.566.7, Vínculo 2 - "
            "ROSELI DE BRITO CABRAL, Professor de Ensino Fundamental II e "
            "Médio - Categoria 3, os efeitos da Port. 89000, de S.M.E., "
            f"D.O.C. de 30/10/2026, SEI nº {_SEI}, que cessou os efeitos da "
            "Port. nº 88000, de S.M.E., D.O.C. de 26/10/2026, SEI nº "
            f"{_SEI}, pela qual o(a) servidor(a) foi designado(a) em "
            "substituição a ISIS OSTI DE MEDEIROS, Diretor de Escola, "
            "registro nº 745.336.1, vínculo 3, no CEI Jardim Primavera I, "
            "durante seu impedimento legal, a partir de 05/02/2026."
        )

    def test_de_designacao_por_impedimento(self, db):
        ferias, _ = ImpedimentoSubstituicao.objects.get_or_create(
            codigo="FERIAS", defaults={"descricao": "Por férias"}
        )
        designacao = _designacao(
            **_TITULAR,
            impedimento_substituicao=ferias,
            data_inicio=datetime.date(2026, 10, 10),
            data_fim=datetime.date(2026, 11, 1),
        )
        insub = criar_ato_insubsistencia(designacao, numero_portaria=10000)
        corpo = _corpo(insub)
        assert "que cessou" not in corpo
        assert (
            "os efeitos da Port. 88000, de S.M.E., D.O.C. de 26/10/2026, "
            f"SEI nº {_SEI}, pela qual o(a) servidor(a) foi designado(a) em "
            "substituição a ISIS OSTI DE MEDEIROS"
        ) in corpo
        assert corpo.endswith(
            "no CEI Jardim Primavera I, por férias, no período de "
            "10/10/2026 a 01/11/2026."
        )

    def test_de_designacao_cargo_vago(self, designacao_vaga):
        insub = criar_ato_insubsistencia(designacao_vaga)
        assert _corpo(insub).endswith(
            "foi designado(a) para exercer o cargo de Diretor de Escola, no "
            "CEI Jardim Primavera I, a partir de 05/02/2026."
        )

    def test_de_insubsistencia(self, designacao_vaga):
        insub = criar_ato_insubsistencia(designacao_vaga, numero_portaria=1)
        insub_de_insub = criar_ato_insubsistencia(insub, numero_portaria=2)
        assert _corpo(insub_de_insub).endswith(
            "os efeitos da Port. 1, de S.M.E., D.O.C. de __/__/____, "
            "SEI nº SEI-I."
        )


# ─── montar_documento / gerar ─────────────────────────────────────────────────


class TestMontarDocumento:
    """Estrutura neutra entregue aos renderers."""

    def test_uma_secao_por_ato_na_ordem_recebida(self, designacao_vaga):
        cessacao = criar_ato_cessacao(designacao_vaga)
        documento = LaudaService.montar_documento([cessacao, designacao_vaga])
        assert documento.titulo == LaudaService.TITULO
        assert [s.titulo for s in documento.secoes] == [
            "FAZENDO CESSAR",
            "DESIGNANDO",
        ]

    def test_cargo_sem_cadastro_fica_vazio(self, db):
        ato = _designacao(cargo_vaga=9999)
        corpo = _corpo(ato)
        assert "para exercer o cargo de , no CEI" in corpo
        assert corpo.endswith("a partir de 05/02/2026.")

    def test_trechos_sao_texto_puro(self, db):
        ato = _designacao(indicado_nome_servidor="A <b>B</b>")
        assert Trecho("A <b>B</b>", negrito=True) in _secao(ato).corpo


class TestGerar:
    """Geração do arquivo final em cada formato."""

    def test_gera_pdf(self, designacao_vaga):
        apostila = criar_ato_apostila(designacao_vaga)
        arquivo = LaudaService.gerar(
            [designacao_vaga.pk, apostila.pk], FormatoLauda.PDF
        )
        assert arquivo.conteudo.startswith(b"%PDF-")
        assert arquivo.content_type == CONTENT_TYPE_PDF
        assert arquivo.nome.endswith(".pdf")

    def test_gera_word(self, designacao_vaga):
        arquivo = LaudaService.gerar([designacao_vaga.pk], FormatoLauda.WORD)
        # .docx é um zip
        assert arquivo.conteudo.startswith(b"PK")
        assert arquivo.content_type == CONTENT_TYPE_DOCX
        assert arquivo.nome.endswith(".docx")

    def test_formato_desconhecido(self, designacao_vaga):
        with pytest.raises(KeyError):
            LaudaService.gerar([designacao_vaga.pk], "ODT")

    def test_propaga_erro_de_validacao(self, db):
        with pytest.raises(ValidationError):
            LaudaService.gerar([99999], FormatoLauda.PDF)

    def test_nome_arquivo_segue_padrao(self):
        nome = LaudaService.nome_arquivo("docx")
        assert nome.startswith("lauda-")
        # lauda-AAAA-MM-DD_HH-mm-ss.docx
        assert len(nome) == len("lauda-2026-09-18_10-23-31.docx")
