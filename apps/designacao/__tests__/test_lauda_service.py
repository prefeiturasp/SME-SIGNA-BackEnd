"""Testes do serviço de geração da lauda de publicação no D.O.

Cobre a seleção/validação dos atos (existência, status de publicação e
texto SEI), a quebra do texto em parágrafos/linhas, a montagem da
estrutura neutra e a geração do arquivo em cada formato.
"""

import pytest
from rest_framework.exceptions import ValidationError

from apps.designacao.models.ato_administrativo import AtoAdministrativo
from apps.designacao.services.lauda_renderers import (
    CONTENT_TYPE_DOCX,
    CONTENT_TYPE_PDF,
    Trecho,
)
from apps.designacao.services.lauda_service import (
    FormatoLauda,
    LaudaService,
)

# ─── Fixtures ─────────────────────────────────────────────────────────────────


def _criar_ato(**kwargs) -> AtoAdministrativo:
    defaults = {
        "tipo": AtoAdministrativo.Tipo.DESIGNACAO,
        "numero_portaria": 10,
        "ano_vigente": "2026",
        "sei_numero": "6018.2026/0000010-0",
        "texto_sei": "<p>Texto da portaria dez.</p>",
    }
    defaults.update(kwargs)
    return AtoAdministrativo.objects.create(**defaults)


@pytest.fixture
def ato_10(db):
    return _criar_ato()


@pytest.fixture
def ato_5(db):
    return _criar_ato(
        numero_portaria=5,
        sei_numero="6018.2026/0000005-0",
        texto_sei="<p>Texto da portaria cinco.</p>",
    )


@pytest.fixture
def apostila(db, ato_10):
    return _criar_ato(
        tipo=AtoAdministrativo.Tipo.APOSTILA,
        ato_pai=ato_10,
        ato_raiz=ato_10,
        numero_portaria=None,
        ano_vigente="",
        sei_numero="6018.2026/0000099-0",
        texto_sei="<p>Texto da apostila.</p>",
    )


@pytest.fixture
def publicado(db):
    return _criar_ato(
        numero_portaria=7,
        sei_numero="6018.2026/0000007-0",
        status_publicacao=AtoAdministrativo.StatusPublicacao.PUBLICADO,
        doc="2026-01-10",
    )


def _detail(exc) -> str:
    return str(exc.value.detail["detail"])


def _textos(blocos) -> list[list[str]]:
    """Achata os trechos em texto: parágrafos → linhas → str."""
    return [
        ["".join(trecho.texto for trecho in linha) for linha in paragrafo]
        for paragrafo in blocos
    ]


def _blocos(texto: str) -> list[list[str]]:
    return _textos(LaudaService.blocos(texto))


# ─── buscar_atos ──────────────────────────────────────────────────────────────


class TestBuscarAtos:
    """Seleção e validação dos atos que compõem a lauda."""

    def test_ordena_por_numero_portaria_com_apostila_por_ultimo(
        self, ato_10, ato_5, apostila
    ):
        atos = LaudaService.buscar_atos([apostila.pk, ato_10.pk, ato_5.pk])
        assert [a.pk for a in atos] == [ato_5.pk, ato_10.pk, apostila.pk]

    def test_erro_id_inexistente(self, ato_10):
        with pytest.raises(ValidationError) as exc:
            LaudaService.buscar_atos([ato_10.pk, 99999])
        assert _detail(exc) == "Atos não encontrados: 99999."

    def test_ato_publicado_entra_na_lauda(self, ato_10, publicado):
        # Sem trava por status_publicacao por enquanto (ver TODO em
        # buscar_atos).
        atos = LaudaService.buscar_atos([ato_10.pk, publicado.pk])
        assert [a.pk for a in atos] == [publicado.pk, ato_10.pk]

    def test_erro_ato_sem_texto_sei(self, ato_10):
        vazio = _criar_ato(
            numero_portaria=11,
            sei_numero="6018.2026/0000011-0",
            texto_sei="   \n",
        )
        with pytest.raises(ValidationError) as exc:
            LaudaService.buscar_atos([ato_10.pk, vazio.pk])
        assert _detail(exc) == "Sem texto SEI: Portaria nº 11/2026."

    def test_erro_usa_chave_detail_e_nao_ids(self, ato_10):
        with pytest.raises(ValidationError) as exc:
            LaudaService.buscar_atos([ato_10.pk, 99999])
        assert set(exc.value.detail) == {"detail"}

    def test_nao_publicado_com_doc_nulo_passa(self, ato_10):
        assert LaudaService.buscar_atos([ato_10.pk]) == [ato_10]


# ─── titulo_ato / blocos ──────────────────────────────────────────────────────


class TestFormatacao:
    """Cabeçalho de cada ato e conversão do HTML do texto SEI em blocos."""

    def test_titulo_com_numero_de_portaria(self, ato_10):
        assert (
            LaudaService.titulo_ato(ato_10)
            == "PORTARIA Nº 10/2026 – DESIGNAÇÃO"
        )

    def test_titulo_apostila_sem_numero(self, apostila):
        assert LaudaService.titulo_ato(apostila) == "APOSTILA"

    def test_rotulo_de_erro_apostila_usa_sei(self, ato_10, apostila):
        apostila.texto_sei = ""
        apostila.save()
        with pytest.raises(ValidationError) as exc:
            LaudaService.buscar_atos([ato_10.pk, apostila.pk])
        assert "Apostila SEI 6018.2026/0000099-0" in _detail(exc)

    def test_blocos_html_paragrafos(self):
        assert _blocos("<p>Primeiro.</p><p>Segundo.</p>") == [
            ["Primeiro."],
            ["Segundo."],
        ]

    def test_blocos_html_br_vira_linha(self):
        assert _blocos("<p>Linha 1<br>Linha 2<br/>Linha 3</p>") == [
            ["Linha 1", "Linha 2", "Linha 3"]
        ]

    def test_blocos_html_negrito_italico_sublinhado(self):
        html = "<p><strong>Negrito</strong> e <em>itálico</em> <u>sub</u></p>"
        (linha,) = LaudaService.blocos(html)[0]
        assert linha == [
            Trecho("Negrito", negrito=True),
            Trecho(" e "),
            Trecho("itálico", italico=True),
            Trecho(" "),
            Trecho("sub", sublinhado=True),
        ]

    def test_blocos_html_aceita_b_e_i(self):
        (linha,) = LaudaService.blocos("<p><b>N</b> <i>I</i></p>")[0]
        assert linha == [
            Trecho("N", negrito=True),
            Trecho(" "),
            Trecho("I", italico=True),
        ]

    def test_blocos_html_formatacao_aninhada(self):
        html = "<p><strong>Negrito <em>e itálico</em></strong> normal</p>"
        (linha,) = LaudaService.blocos(html)[0]
        assert linha == [
            Trecho("Negrito ", negrito=True),
            Trecho("e itálico", negrito=True, italico=True),
            Trecho(" normal"),
        ]

    def test_blocos_html_funde_trechos_vizinhos_iguais(self):
        (linha,) = LaudaService.blocos("<p><b>A</b><b>B</b>C</p>")[0]
        assert linha == [Trecho("AB", negrito=True), Trecho("C")]

    def test_blocos_html_formatacao_atravessa_br(self):
        html = "<p><strong>Linha 1<br>Linha 2</strong></p>"
        (paragrafo,) = LaudaService.blocos(html)
        assert paragrafo == [
            [Trecho("Linha 1", negrito=True)],
            [Trecho("Linha 2", negrito=True)],
        ]

    def test_blocos_html_descarta_outras_tags_inline(self):
        html = '<p><span style="color:red">Cor</span> <a href="#">link</a></p>'
        assert _blocos(html) == [["Cor link"]]

    def test_blocos_html_decodifica_entidades(self):
        html = "<p>a&nbsp;&amp;&nbsp;b &lt; c &aacute;</p>"
        assert _blocos(html) == [["a & b < c á"]]

    def test_blocos_html_colapsa_espacos_e_quebras_de_fonte(self):
        html = "<p>\n  Texto   com\n  espaços  \n</p>\n\n<p>Outro</p>"
        assert _blocos(html) == [["Texto com espaços"], ["Outro"]]

    def test_blocos_html_nao_duplica_espaco_entre_trechos(self):
        html = "<p><b>A </b> <i> B</i></p>"
        assert _blocos(html) == [["A B"]]

    def test_blocos_html_ignora_paragrafos_vazios(self):
        html = "<p></p><p>&nbsp;</p><p>Só este</p><p><br></p>"
        assert _blocos(html) == [["Só este"]]

    def test_blocos_html_listas(self):
        html = (
            "<ol><li>Um</li><li>Dois</li></ol>"
            "<ul><li>Bala</li></ul><p>Fim</p>"
        )
        assert _blocos(html) == [["1. Um"], ["2. Dois"], ["• Bala"], ["Fim"]]

    def test_blocos_html_li_fora_de_lista_vira_paragrafo_sem_marcador(self):
        # HTML malformado do editor: <li> solto não ganha "•" nem "1."
        assert _blocos("<p>A</p><li>Solto</li><p>B</p>") == [
            ["A"],
            ["Solto"],
            ["B"],
        ]

    def test_blocos_html_marcador_de_lista_nao_herda_formatacao(self):
        (linha,) = LaudaService.blocos("<ul><li><b>Item</b></li></ul>")[0]
        assert linha == [Trecho("• "), Trecho("Item", negrito=True)]

    def test_blocos_html_ignora_script_e_style(self):
        html = "<style>p{}</style><p>Ok</p><script>x()</script>"
        assert _blocos(html) == [["Ok"]]

    def test_blocos_texto_puro_legado(self):
        texto = "Primeiro.\nLinha 2.\n\n\n\nSegundo."
        assert _blocos(texto) == [["Primeiro.", "Linha 2."], ["Segundo."]]

    def test_blocos_texto_puro_sem_formatacao(self):
        (linha,) = LaudaService.blocos("Texto puro")[0]
        assert linha == [Trecho("Texto puro")]

    def test_blocos_texto_puro_normaliza_crlf(self):
        assert _blocos("A\r\nB\r\n\r\nC") == [["A", "B"], ["C"]]

    def test_blocos_texto_puro_ignora_espacos_nas_pontas(self):
        assert _blocos("  \n\n Texto \n\n ") == [["Texto"]]

    def test_blocos_saida_e_texto_puro_sem_escape(self):
        # Quem escapa é o renderer (PDF); o Word grava literal.
        assert _blocos("<p>x &lt; y</p>") == [["x < y"]]


# ─── montar_documento ─────────────────────────────────────────────────────────


class TestMontarDocumento:
    """Estrutura neutra entregue aos renderers."""

    def test_aviso_titulo_sei_e_subtitulo(self, ato_10, ato_5):
        documento = LaudaService.montar_documento([ato_5, ato_10])
        assert documento.aviso == LaudaService.AVISO_DESENVOLVIMENTO
        assert documento.titulo == LaudaService.TITULO
        assert documento.sei == LaudaService.SEI_LAUDA
        assert documento.subtitulo.startswith("Gerada em ")
        assert documento.subtitulo.endswith("2 ato(s)")

    def test_uma_secao_por_ato_na_ordem_recebida(self, ato_10, ato_5):
        documento = LaudaService.montar_documento([ato_5, ato_10])
        assert [s.titulo for s in documento.secoes] == [
            "PORTARIA Nº 5/2026 – DESIGNAÇÃO",
            "PORTARIA Nº 10/2026 – DESIGNAÇÃO",
        ]
        assert documento.secoes[0].sei == "6018.2026/0000005-0"
        assert documento.secoes[0].blocos == [
            [[Trecho("Texto da portaria cinco.")]]
        ]


# ─── gerar ────────────────────────────────────────────────────────────────────


class TestGerar:
    """Geração do arquivo final em cada formato."""

    def test_gera_pdf(self, ato_10, ato_5, apostila):
        arquivo = LaudaService.gerar(
            [ato_10.pk, ato_5.pk, apostila.pk], FormatoLauda.PDF
        )
        assert arquivo.conteudo.startswith(b"%PDF-")
        assert arquivo.content_type == CONTENT_TYPE_PDF
        assert arquivo.nome.endswith(".pdf")

    def test_gera_word(self, ato_10, ato_5, apostila):
        arquivo = LaudaService.gerar(
            [ato_10.pk, ato_5.pk, apostila.pk], FormatoLauda.WORD
        )
        # .docx é um zip
        assert arquivo.conteudo.startswith(b"PK")
        assert arquivo.content_type == CONTENT_TYPE_DOCX
        assert arquivo.nome.endswith(".docx")

    def test_formato_desconhecido(self, ato_10):
        with pytest.raises(KeyError):
            LaudaService.gerar([ato_10.pk], "ODT")

    def test_propaga_erro_de_validacao(self, db):
        with pytest.raises(ValidationError):
            LaudaService.gerar([99999], FormatoLauda.PDF)

    def test_nome_arquivo_segue_padrao(self):
        nome = LaudaService.nome_arquivo("docx")
        assert nome.startswith("lauda-")
        # lauda-AAAA-MM-DD_HH-mm-ss.docx
        assert len(nome) == len("lauda-2026-09-18_10-23-31.docx")
