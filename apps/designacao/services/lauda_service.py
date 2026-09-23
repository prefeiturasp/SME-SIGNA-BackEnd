"""Serviço de geração da lauda de publicação no Diário Oficial.

Monta um único arquivo (PDF ou Word) com o texto SEI de todos os atos
selecionados na tela de publicação. O texto vem de
``AtoAdministrativo.texto_sei`` — já congelado na emissão do ato — e por
isso não é regerado a partir do modelo de portaria.

Atos já publicados também podem compor a lauda — a trava por
``status_publicacao`` ficou comentada em ``buscar_atos`` até a regra ser
confirmada.
"""

import re
from collections.abc import Callable
from dataclasses import dataclass, replace
from html.parser import HTMLParser

from django.db import models
from django.db.models import F
from django.utils import timezone

from apps.designacao.models.ato_administrativo import AtoAdministrativo
from apps.designacao.services.lauda_renderers import (
    CONTENT_TYPE_DOCX,
    CONTENT_TYPE_PDF,
    DocumentoLauda,
    Linha,
    Paragrafo,
    SecaoLauda,
    Trecho,
    renderizar_docx,
    renderizar_pdf,
)

# Texto puro: quebra de parágrafo (linha em branco) ou de linha.
_QUEBRAS_TEXTO_PURO = re.compile(r"(\n[ \t]*\n\s*|\n)")
# Espaços horizontais (inclui NBSP vindo de &nbsp;) a colapsar numa linha.
_ESPACOS = re.compile(r"[ \t\xa0\f\v]+")
# Qualquer tag HTML: decide se o texto é HTML do editor ou texto puro.
_TEM_TAG = re.compile(r"<[a-zA-Z/][^>]*>")


class FormatoLauda(models.TextChoices):
    """Formatos de arquivo suportados pela lauda."""

    PDF = "PDF", "PDF"
    WORD = "WORD", "Word"


@dataclass(frozen=True)
class ArquivoLauda:
    """Arquivo gerado, pronto para ser devolvido como anexo."""

    conteudo: bytes
    nome: str
    content_type: str


@dataclass(frozen=True)
class _Renderer:
    renderizar: Callable[[DocumentoLauda], bytes]
    content_type: str
    extensao: str


_RENDERERS: dict[str, _Renderer] = {
    FormatoLauda.PDF: _Renderer(renderizar_pdf, CONTENT_TYPE_PDF, "pdf"),
    FormatoLauda.WORD: _Renderer(renderizar_docx, CONTENT_TYPE_DOCX, "docx"),
}


class LaudaService:
    """Gera a lauda a partir dos atos selecionados."""

    TITULO = "PORTARIAS EXPEDIDAS PELO SECRETÁRIO"
    # TO-DO: remover quando os textos finais da lauda estiverem definidos.
    AVISO_DESENVOLVIMENTO = (
        "Versão inicial de desenvolvimento, ainda não traz os textos "
        "finais de lauda"
    )
    # TO-DO: definir de onde vem o número SEI da lauda (não é o do ato).
    SEI_LAUDA = "xxxxxxxxxxxxxxx"

    @staticmethod
    def gerar(ids: list[int], formato: str) -> ArquivoLauda:
        """Gera o arquivo da lauda no formato pedido.

        Args:
            ids: IDs dos atos administrativos selecionados.
            formato: Um dos valores de ``FormatoLauda``.

        Returns:
            ArquivoLauda: Bytes, nome e content-type do arquivo.

        Raises:
            ValidationError: Quando algum id não existe ou não possui
                texto SEI.
            KeyError: Formato não suportado (o serializer já barra
                antes de chegar aqui).

        """
        renderer = _RENDERERS[formato]
        atos = LaudaService.buscar_atos(ids)
        documento = LaudaService.montar_documento(atos)
        return ArquivoLauda(
            conteudo=renderer.renderizar(documento),
            nome=LaudaService.nome_arquivo(renderer.extensao),
            content_type=renderer.content_type,
        )

    @staticmethod
    def nome_arquivo(extensao: str) -> str:
        """Nome do arquivo no padrão ``lauda-AAAA-MM-DD_HH-mm-ss.<ext>``.

        Args:
            extensao: Extensão sem ponto (``pdf``, ``docx``).

        Returns:
            str: Nome do arquivo com carimbo de data/hora local.

        """
        agora = timezone.localtime()
        return f"lauda-{agora:%Y-%m-%d_%H-%M-%S}.{extensao}"

    @staticmethod
    def buscar_atos(ids: list[int]) -> list[AtoAdministrativo]:
        """Carrega e valida os atos que vão compor a lauda.

        Os erros de regra de negócio são levantados com a chave
        ``detail`` — são do lote, não do campo ``ids`` — para que o
        front receba a frase pura, sem prefixo de campo.

        Args:
            ids: IDs dos atos administrativos selecionados.

        Returns:
            list[AtoAdministrativo]: Atos ordenados por número de
            portaria (apostilas, sem número, ficam por último).

        Raises:
            ValidationError: Quando algum id não existe ou não possui
                texto SEI.

        """
        # Import local para evitar dependência do DRF no módulo inteiro.
        from rest_framework.exceptions import ValidationError

        atos = list(
            AtoAdministrativo.objects.filter(pk__in=ids).order_by(
                F("numero_portaria").asc(nulls_last=True), "pk"
            )
        )

        encontrados = {ato.pk for ato in atos}
        faltando = sorted(set(ids) - encontrados)
        if faltando:
            raise ValidationError(
                {"detail": f"Atos não encontrados: {_listar(faltando)}."}
            )

        # TO-DO: confirmar com a área se ato já publicado pode voltar para
        # a lauda (reimpressão/republicação). Por ora não há trava; se a
        # regra for de bloqueio, basta reativar o trecho abaixo.
        # publicados = [
        #     ato
        #     for ato in atos
        #     if ato.status_publicacao
        #     == AtoAdministrativo.StatusPublicacao.PUBLICADO
        # ]
        # if publicados:
        #     raise ValidationError(
        #         {
        #             "detail": (
        #                 "Já publicados, não podem compor a lauda: "
        #                 f"{_listar_atos(publicados)}."
        #             )
        #         }
        #     )

        sem_texto = [ato for ato in atos if not ato.texto_sei.strip()]
        if sem_texto:
            raise ValidationError(
                {"detail": f"Sem texto SEI: {_listar_atos(sem_texto)}."}
            )

        return atos

    @staticmethod
    def montar_documento(atos: list[AtoAdministrativo]) -> DocumentoLauda:
        """Monta a estrutura neutra consumida pelos renderers.

        Args:
            atos: Atos já validados e ordenados.

        Returns:
            DocumentoLauda: Aviso, título, SEI, subtítulo e uma seção
            por ato.

        """
        agora = timezone.localtime()
        return DocumentoLauda(
            aviso=LaudaService.AVISO_DESENVOLVIMENTO,
            titulo=LaudaService.TITULO,
            sei=LaudaService.SEI_LAUDA,
            subtitulo=(
                f"Gerada em {agora:%d/%m/%Y às %H:%M} — {len(atos)} ato(s)"
            ),
            secoes=[
                SecaoLauda(
                    titulo=LaudaService.titulo_ato(ato),
                    sei=ato.sei_numero,
                    blocos=LaudaService.blocos(ato.texto_sei),
                )
                for ato in atos
            ],
        )

    # TO-DO: Quando terminar desenvolvimento verificar se deve remover
    @staticmethod
    def titulo_ato(ato: AtoAdministrativo) -> str:
        """Cabeçalho de um ato dentro da lauda.

        Args:
            ato: Ato administrativo.

        Returns:
            str: ``PORTARIA Nº 12/2024 – DESIGNAÇÃO`` para atos com
            número de portaria; só o tipo (``APOSTILA``) para os demais.
            O número SEI aparece na linha seguinte, para todos.

        """
        tipo = ato.get_tipo_display().upper()
        if ato.numero_portaria is None:
            return tipo
        return f"PORTARIA Nº {ato.numero_portaria}/{ato.ano_vigente} – {tipo}"

    @staticmethod
    def blocos(texto: str) -> list[Paragrafo]:
        """Quebra o texto SEI em parágrafos, linhas e trechos formatados.

        O texto SEI é o HTML do editor rich text do modelo de portaria.
        Tags de bloco viram parágrafos, ``<br>`` vira linha, itens de
        lista ganham marcador; ``<strong>/<b>``, ``<em>/<i>`` e ``<u>``
        viram negrito, itálico e sublinhado nos trechos, e as demais
        tags são descartadas. Quebras de linha do fonte HTML são só
        espaço, como no browser. Texto sem nenhuma tag (legado) segue a
        regra de texto puro: linhas em branco separam parágrafos e
        quebras simples separam linhas.

        Args:
            texto: Texto SEI do ato (HTML ou texto puro).

        Returns:
            list[Paragrafo]: Parágrafos → linhas → trechos.

        """
        normalizado = texto.replace("\r\n", "\n").replace("\r", "\n")
        extrator = _ExtratorTexto(html=bool(_TEM_TAG.search(normalizado)))
        extrator.feed(normalizado)
        extrator.close()
        return extrator.finalizar()


class _ExtratorTexto(HTMLParser):
    """Reduz o HTML do editor a parágrafos de trechos formatados.

    Entidades já chegam decodificadas em ``handle_data``
    (``convert_charrefs=True``, padrão do ``HTMLParser``).
    """

    _BLOCOS = frozenset(
        {
            "p",
            "div",
            "h1",
            "h2",
            "h3",
            "h4",
            "h5",
            "h6",
            "blockquote",
            "pre",
            "table",
            "tr",
            "section",
            "article",
        }
    )
    _IGNORADAS = frozenset({"script", "style"})
    _TAGS_NEGRITO = frozenset({"b", "strong"})
    _TAGS_ITALICO = frozenset({"i", "em"})
    _TAGS_SUBLINHADO = frozenset({"u"})

    def __init__(self, html: bool) -> None:
        super().__init__()
        # Em HTML, "\n" do fonte é espaço; em texto puro, é quebra de linha.
        self._html = html
        self._paragrafos: list[Paragrafo] = []
        self._paragrafo: Paragrafo = []
        self._linha: Linha = []
        # Profundidade de cada formatação (tags podem se aninhar/repetir).
        self._negrito = 0
        self._italico = 0
        self._sublinhado = 0
        # Pilha de listas abertas: contador para <ol>, None para <ul>.
        self._listas: list[int | None] = []
        self._ignorando = 0

    # ── saída ──

    def finalizar(self) -> list[Paragrafo]:
        self._fechar_paragrafo()
        return self._paragrafos

    # ── eventos do parser ──

    def handle_starttag(
        self, tag: str, attrs: list[tuple[str, str | None]]
    ) -> None:
        if tag in self._IGNORADAS:
            self._ignorando += 1
        elif tag == "br":
            self._fechar_linha()
        elif tag == "ol":
            self._listas.append(0)
            self._fechar_paragrafo()
        elif tag == "ul":
            self._listas.append(None)
            self._fechar_paragrafo()
        elif tag == "li":
            self._fechar_paragrafo()
            self._adicionar(self._marcador(), formatado=False)
        elif tag in self._BLOCOS:
            self._fechar_paragrafo()
        elif tag in self._TAGS_NEGRITO:
            self._negrito += 1
        elif tag in self._TAGS_ITALICO:
            self._italico += 1
        elif tag in self._TAGS_SUBLINHADO:
            self._sublinhado += 1

    def handle_endtag(self, tag: str) -> None:
        if tag in self._IGNORADAS:
            self._ignorando = max(0, self._ignorando - 1)
        elif tag in ("ol", "ul"):
            if self._listas:
                self._listas.pop()
            self._fechar_paragrafo()
        elif tag == "li" or tag in self._BLOCOS:
            self._fechar_paragrafo()
        elif tag in self._TAGS_NEGRITO:
            self._negrito = max(0, self._negrito - 1)
        elif tag in self._TAGS_ITALICO:
            self._italico = max(0, self._italico - 1)
        elif tag in self._TAGS_SUBLINHADO:
            self._sublinhado = max(0, self._sublinhado - 1)

    def handle_data(self, data: str) -> None:
        if self._ignorando:
            return
        if self._html:
            self._adicionar(data.replace("\n", " "))
            return
        # Texto puro: as quebras do próprio texto estruturam o conteúdo.
        for parte in _QUEBRAS_TEXTO_PURO.split(data):
            if not parte:
                continue
            if parte == "\n":
                self._fechar_linha()
            elif parte.startswith("\n"):
                self._fechar_paragrafo()
            else:
                self._adicionar(parte)

    # ── montagem ──

    def _adicionar(self, texto: str, formatado: bool = True) -> None:
        if not texto:
            return
        self._linha.append(
            Trecho(
                texto=texto,
                negrito=formatado and self._negrito > 0,
                italico=formatado and self._italico > 0,
                sublinhado=formatado and self._sublinhado > 0,
            )
        )

    def _fechar_linha(self) -> None:
        linha = _normalizar_linha(self._linha)
        self._linha = []
        if linha:
            self._paragrafo.append(linha)

    def _fechar_paragrafo(self) -> None:
        self._fechar_linha()
        if self._paragrafo:
            self._paragrafos.append(self._paragrafo)
            self._paragrafo = []

    def _marcador(self) -> str:
        if not self._listas:
            return ""
        contador = self._listas[-1]
        if contador is None:
            return "• "
        self._listas[-1] = contador + 1
        return f"{contador + 1}. "


def _normalizar_linha(linha: Linha) -> Linha:
    """Colapsa espaços, funde trechos vizinhos iguais e apara as pontas."""
    resultado: Linha = []
    for trecho in linha:
        texto = _ESPACOS.sub(" ", trecho.texto)
        if resultado and resultado[-1].texto.endswith(" "):
            texto = texto.lstrip(" ")
        if not texto:
            continue
        anterior = resultado[-1] if resultado else None
        if anterior is not None and _mesma_formatacao(anterior, trecho):
            resultado[-1] = replace(anterior, texto=anterior.texto + texto)
        else:
            resultado.append(replace(trecho, texto=texto))

    if resultado:
        resultado[0] = replace(resultado[0], texto=resultado[0].texto.lstrip())
        resultado[-1] = replace(
            resultado[-1], texto=resultado[-1].texto.rstrip()
        )
    return [trecho for trecho in resultado if trecho.texto]


def _mesma_formatacao(a: Trecho, b: Trecho) -> bool:
    return (a.negrito, a.italico, a.sublinhado) == (
        b.negrito,
        b.italico,
        b.sublinhado,
    )


def _listar(ids: list[int]) -> str:
    return ", ".join(str(i) for i in ids)


def _rotulo(ato: AtoAdministrativo) -> str:
    """Identificação legível do ato para mensagens de erro.

    Args:
        ato: Ato administrativo.

    Returns:
        str: ``Portaria nº 12/2026`` quando há número; caso contrário
        (apostila) ``Apostila SEI 6018...``.

    """
    if ato.numero_portaria is None:
        return f"{ato.get_tipo_display()} SEI {ato.sei_numero}"
    return f"Portaria nº {ato.numero_portaria}/{ato.ano_vigente}"


def _listar_atos(atos: list[AtoAdministrativo]) -> str:
    return ", ".join(_rotulo(ato) for ato in atos)
