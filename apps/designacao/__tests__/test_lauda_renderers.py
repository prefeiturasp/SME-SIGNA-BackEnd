"""Testes dos renderizadores da lauda (PDF via ReportLab, Word via python-docx).

Trabalham sobre um ``DocumentoLauda`` fixo, sem banco: verificam que o
conteúdo chega ao arquivo, que o PDF escapa markup e que o Word preserva
o texto literalmente.
"""

import csv
from io import BytesIO, StringIO

import pytest
from docx import Document
from reportlab.platypus import Paragraph

from apps.designacao.services.lauda_renderers import (
    DocumentoLauda,
    SecaoLauda,
    Trecho,
    montar_story,
    renderizar_csv,
    renderizar_docx,
    renderizar_pdf,
)

TEXTO_COM_MARKUP = "Cargo <b>X</b> & <img src='file:///etc/passwd'/>"


@pytest.fixture
def documento() -> DocumentoLauda:
    return DocumentoLauda(
        titulo="Lauda de teste",
        secoes=[
            SecaoLauda(
                titulo="DESIGNANDO",
                dre="Diretoria Regional de Educação BUTANTA",
                corpo=[
                    Trecho("Port. 5/2026 -", negrito=True),
                    Trecho(" Fim "),
                    Trecho("itálico", italico=True),
                    Trecho(" "),
                    Trecho("ambos", negrito=True, italico=True),
                    Trecho(" "),
                    Trecho("sub", sublinhado=True),
                    Trecho("."),
                ],
            ),
            SecaoLauda(
                titulo="APOSTILANDO",
                dre="Diretoria Regional de Educação BUTANTA",
                corpo=[Trecho(TEXTO_COM_MARKUP)],
            ),
        ],
    )


def _paragrafos(flowables) -> list[Paragraph]:
    return [item for item in flowables if isinstance(item, Paragraph)]


def _textos(flowables) -> list[str]:
    return [p.text for p in _paragrafos(flowables)]


CORPO_PDF = (
    "<b>Port. 5/2026 -</b> Fim <i>itálico</i> <i><b>ambos</b></i> <u>sub</u>."
)
CORPO_DOCX = "Port. 5/2026 - Fim itálico ambos sub."


class TestPdf:
    """Renderização em PDF."""

    def test_story_titulo_dre_e_corpo(self, documento):
        textos = _textos(montar_story(documento))
        assert textos == [
            "DESIGNANDO",
            "Diretoria Regional de Educação BUTANTA",
            CORPO_PDF,
            "APOSTILANDO",
            "Diretoria Regional de Educação BUTANTA",
            textos[-1],
        ]

    def test_story_titulo_e_dre_em_negrito(self, documento):
        titulo, dre = _paragrafos(montar_story(documento))[:2]
        assert titulo.style.fontName == "Helvetica-Bold"
        assert dre.style.fontName == "Helvetica-Bold"

    def test_story_escapa_markup(self, documento):
        # O parser de Paragraph do ReportLab interpreta tags — texto do
        # banco nunca pode chegar cru.
        textos = _textos(montar_story(documento))
        assert not any("<img" in t for t in textos)
        assert any("&lt;b&gt;X&lt;/b&gt; &amp;" in t for t in textos)

    def test_gera_pdf_valido(self, documento):
        pdf = renderizar_pdf(documento)
        assert pdf.startswith(b"%PDF-")
        assert b"%%EOF" in pdf[-64:]


class TestDocx:
    """Renderização em Word."""

    @pytest.fixture
    def docx(self, documento):
        return Document(BytesIO(renderizar_docx(documento)))

    def test_titulo_dre_e_corpo(self, docx):
        textos = [p.text for p in docx.paragraphs]
        assert textos == [
            "DESIGNANDO",
            "Diretoria Regional de Educação BUTANTA",
            CORPO_DOCX,
            "",
            "APOSTILANDO",
            "Diretoria Regional de Educação BUTANTA",
            TEXTO_COM_MARKUP,
            "",
        ]

    def test_titulo_e_dre_em_negrito(self, docx):
        for paragrafo in docx.paragraphs[:2]:
            (run,) = paragrafo.runs
            assert run.bold

    def test_formatacao_dos_runs(self, docx):
        runs = {r.text: r for r in docx.paragraphs[2].runs}
        assert runs["Port. 5/2026 -"].bold
        assert runs["itálico"].italic and not runs["itálico"].bold
        assert runs["ambos"].bold and runs["ambos"].italic
        assert runs["sub"].underline
        assert not runs[" Fim "].bold and not runs[" Fim "].italic

    def test_texto_preservado_literalmente(self, docx):
        # python-docx grava texto, não markup — nada a escapar.
        assert TEXTO_COM_MARKUP in [p.text for p in docx.paragraphs]

    def test_rodape_tem_campo_de_pagina(self, docx):
        rodape = docx.sections[0].footer.paragraphs[0]
        assert rodape.text.startswith("Página ")
        assert 'w:instr="PAGE"' in rodape._p.xml

    def test_metadados(self, docx):
        assert docx.core_properties.title == "Lauda de teste"


class TestCsv:
    """Uma linha por ato, legível pelo Excel em pt-BR."""

    def _linhas(self, documento) -> list[list[str]]:
        conteudo = renderizar_csv(documento).decode("utf-8-sig")
        return list(csv.reader(StringIO(conteudo), delimiter=";"))

    def test_comeca_com_bom_utf8(self, documento):
        assert renderizar_csv(documento).startswith(b"\xef\xbb\xbf")

    def test_cabecalho_e_uma_linha_por_secao_na_ordem(self, documento):
        linhas = self._linhas(documento)
        assert linhas[0] == ["Título", "DRE", "Texto"]
        assert [linha[0] for linha in linhas[1:]] == [
            "DESIGNANDO",
            "APOSTILANDO",
        ]

    def test_texto_sem_formatacao(self, documento):
        assert self._linhas(documento)[1] == [
            "DESIGNANDO",
            "Diretoria Regional de Educação BUTANTA",
            CORPO_DOCX,
        ]

    def test_texto_com_separador_e_aspas_fica_numa_celula(self):
        texto = 'a; b "c"\nd'
        documento = DocumentoLauda(
            titulo="t",
            secoes=[SecaoLauda("DESIGNANDO", "DRE X", [Trecho(texto)])],
        )
        assert self._linhas(documento)[1][2] == texto

    @pytest.mark.parametrize("inicio", ["=", "+", "-", "@"])
    def test_neutraliza_formula(self, inicio):
        documento = DocumentoLauda(
            titulo="t",
            secoes=[
                SecaoLauda("DESIGNANDO", "DRE X", [Trecho(f"{inicio}1+1")])
            ],
        )
        assert self._linhas(documento)[1][2] == f"'{inicio}1+1"
