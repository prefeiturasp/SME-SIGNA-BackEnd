"""Renderizadores da lauda de publicação no D.O. (PDF e Word).

Recebem um ``DocumentoLauda`` já montado pelo ``LaudaService`` e devolvem
os bytes do arquivo. Nenhuma regra de negócio vive aqui — só layout.
"""

from dataclasses import dataclass
from io import BytesIO
from xml.sax.saxutils import escape

from docx import Document
from docx.document import Document as DocxDocument
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import Pt
from docx.text.paragraph import Paragraph as DocxParagraph
from reportlab.lib.enums import TA_CENTER, TA_JUSTIFY
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.pdfgen.canvas import Canvas
from reportlab.platypus import (
    Flowable,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
)

CONTENT_TYPE_PDF = "application/pdf"
CONTENT_TYPE_DOCX = (
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
)

_MARGEM_PDF = 20 * mm


@dataclass(frozen=True)
class Trecho:
    """Um trecho de texto com formatação uniforme (um *run*)."""

    texto: str
    negrito: bool = False
    italico: bool = False
    sublinhado: bool = False


# Uma linha é uma sequência de trechos com formatação própria.
Linha = list[Trecho]


@dataclass(frozen=True)
class SecaoLauda:
    """Um ato dentro da lauda.

    Attributes:
        titulo: Verbo do ato (``DESIGNANDO``, ``APOSTILANDO``...),
            centralizado e em negrito.
        dre: ``Diretoria Regional de Educação X``, centralizado e em
            negrito.
        corpo: Texto do ato, justificado.

    """

    titulo: str
    dre: str
    corpo: Linha


@dataclass(frozen=True)
class DocumentoLauda:
    """Conteúdo completo da lauda, independente de formato.

    Attributes:
        titulo: Título do arquivo (metadado; não é impresso).
        secoes: Um item por ato, na ordem de impressão.

    """

    titulo: str
    secoes: list[SecaoLauda]


# ─── PDF ─────────────────────────────────────────────────────────────────────


def renderizar_pdf(documento: DocumentoLauda) -> bytes:
    """Gera o PDF da lauda com ReportLab.

    Args:
        documento: Conteúdo da lauda.

    Returns:
        bytes: Arquivo PDF.

    """
    buffer = BytesIO()
    pdf = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        leftMargin=_MARGEM_PDF,
        rightMargin=_MARGEM_PDF,
        topMargin=_MARGEM_PDF,
        bottomMargin=_MARGEM_PDF,
        title=documento.titulo,
        author="SIGNA",
    )
    pdf.build(
        montar_story(documento),
        onFirstPage=_rodape_pdf,
        onLaterPages=_rodape_pdf,
    )
    return buffer.getvalue()


def montar_story(documento: DocumentoLauda) -> list[Flowable]:
    """Monta a sequência de elementos do PDF.

    Todo texto passa por ``escape`` antes de virar ``Paragraph`` — o
    parser de markup do ReportLab já teve RCEs por conteúdo não
    confiável, e o texto vem do banco.

    Args:
        documento: Conteúdo da lauda.

    Returns:
        list[Flowable]: Para cada ato: título, DRE e corpo.

    """
    estilos = _estilos_pdf()
    story: list[Flowable] = []
    for secao in documento.secoes:
        story += [
            Paragraph(escape(secao.titulo), estilos["titulo"]),
            Paragraph(escape(secao.dre), estilos["titulo"]),
            Paragraph(_linha_pdf(secao.corpo), estilos["corpo"]),
            Spacer(1, 8 * mm),
        ]

    return story


def _linha_pdf(linha: Linha) -> str:
    """Monta o markup do ``Paragraph`` para uma linha (texto escapado)."""
    partes = []
    for trecho in linha:
        texto = escape(trecho.texto)
        if trecho.negrito:
            texto = f"<b>{texto}</b>"
        if trecho.italico:
            texto = f"<i>{texto}</i>"
        if trecho.sublinhado:
            texto = f"<u>{texto}</u>"
        partes.append(texto)
    return "".join(partes)


def _rodape_pdf(canvas: Canvas, documento: SimpleDocTemplate) -> None:
    largura, _ = documento.pagesize
    canvas.saveState()
    canvas.setFont("Helvetica", 8)
    canvas.drawRightString(
        largura - _MARGEM_PDF, 10 * mm, f"Página {documento.page}"
    )
    canvas.restoreState()


def _estilos_pdf() -> dict[str, ParagraphStyle]:
    base = getSampleStyleSheet()
    return {
        "titulo": ParagraphStyle(
            "LaudaTitulo",
            parent=base["Normal"],
            fontName="Helvetica-Bold",
            fontSize=10,
            leading=14,
            alignment=TA_CENTER,
        ),
        "corpo": ParagraphStyle(
            "LaudaCorpo",
            parent=base["Normal"],
            fontSize=10,
            leading=14,
            alignment=TA_JUSTIFY,
        ),
    }


# ─── Word ────────────────────────────────────────────────────────────────────


def renderizar_docx(documento: DocumentoLauda) -> bytes:
    """Gera o .docx da lauda com python-docx.

    Diferente do ReportLab, ``add_run`` grava o texto literalmente no
    XML (o lxml escapa) — não há markup a neutralizar.

    Args:
        documento: Conteúdo da lauda.

    Returns:
        bytes: Arquivo Word (.docx).

    """
    docx = Document()
    docx.core_properties.title = documento.titulo
    docx.core_properties.author = "SIGNA"

    normal = docx.styles["Normal"]
    normal.font.name = "Arial"
    normal.font.size = Pt(10)

    for secao in documento.secoes:
        _secao_docx(docx, secao)
    _numerar_paginas_docx(docx)

    buffer = BytesIO()
    docx.save(buffer)
    return buffer.getvalue()


def _secao_docx(docx: DocxDocument, secao: SecaoLauda) -> None:
    """Título e DRE centralizados e corpo justificado."""
    for texto in (secao.titulo, secao.dre):
        paragrafo = _paragrafo_compacto(docx, WD_ALIGN_PARAGRAPH.CENTER)
        paragrafo.add_run(texto).bold = True

    corpo = _paragrafo_compacto(docx, WD_ALIGN_PARAGRAPH.JUSTIFY)
    for trecho in secao.corpo:
        run = corpo.add_run(trecho.texto)
        run.bold = trecho.negrito or None
        run.italic = trecho.italico or None
        run.underline = trecho.sublinhado or None

    docx.add_paragraph()


def _paragrafo_compacto(
    docx: DocxDocument, alinhamento: WD_ALIGN_PARAGRAPH
) -> DocxParagraph:
    paragrafo = docx.add_paragraph()
    paragrafo.alignment = alinhamento
    paragrafo.paragraph_format.space_after = Pt(0)
    return paragrafo


def _numerar_paginas_docx(docx: DocxDocument) -> None:
    """Insere ``Página N`` no rodapé via campo ``PAGE`` do Word."""
    rodape = docx.sections[0].footer.paragraphs[0]
    rodape.alignment = WD_ALIGN_PARAGRAPH.RIGHT
    rodape.add_run("Página ").font.size = Pt(8)

    campo = OxmlElement("w:fldSimple")
    campo.set(qn("w:instr"), "PAGE")
    run = OxmlElement("w:r")
    texto = OxmlElement("w:t")
    texto.text = "1"
    run.append(texto)
    campo.append(run)
    rodape._p.append(campo)
