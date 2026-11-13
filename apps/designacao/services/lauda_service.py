"""Serviço de geração da lauda de publicação no Diário Oficial.

Monta um único arquivo (PDF ou Word) com o texto de publicação de todos
os atos selecionados na tela de publicação. Diferente do texto SEI, o
texto da lauda é montado aqui a partir dos dados gravados no banco, com
um formato próprio por tipo de ato (designando, apostilando, fazendo
cessar, tornando insubsistente, tornar sem efeito).

Atos já publicados também podem compor a lauda — a trava por
``status_publicacao`` ficou comentada em ``buscar_atos`` até a regra ser
confirmada.
"""

import datetime
from collections.abc import Callable
from dataclasses import dataclass

from django.db import models
from django.utils import timezone

from apps.designacao.constants.cargos_gestao_escolar import (
    CODIGOS_CARGO_PROFESSOR,
)
from apps.designacao.models.ato_administrativo import AtoAdministrativo
from apps.designacao.models.designacao_detalhe import DesignacaoDetalhe
from apps.designacao.services.lauda_renderers import (
    CONTENT_TYPE_DOCX,
    CONTENT_TYPE_PDF,
    DocumentoLauda,
    Linha,
    SecaoLauda,
    Trecho,
    renderizar_docx,
    renderizar_pdf,
)
from apps.gestao.models.cargo_base import CargoBase

# TO-DO: aguardando a área definir de onde vem a situação funcional
# (efetivo, comissionado...) do indicado e do titular.
SITUACAO_FUNCIONAL = "efetivo"

_DATA_VAZIA = "__/__/____"
_PREFIXOS_DRE = (
    "DIRETORIA REGIONAL DE EDUCAÇÃO",
    "DIRETORIA REGIONAL DE EDUCACAO",
    "DRE",
)
# Unidades cujo tipo é feminino ("na EMEF", "na DRE"); as demais levam
# "no" ("no CEI", "no CEU EMEI").
_UNIDADES_FEMININAS = frozenset(
    {"EMEF", "EMEFM", "EMEI", "EMEBS", "ESCOLA", "DRE", "DIRETORIA"}
)
_ORDEM_TIPOS: list[str] = list(AtoAdministrativo.Tipo)


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

    @staticmethod
    def gerar(ids: list[int], formato: str) -> ArquivoLauda:
        """Gera o arquivo da lauda no formato pedido.

        Args:
            ids: IDs dos atos administrativos selecionados.
            formato: Um dos valores de ``FormatoLauda``.

        Returns:
            ArquivoLauda: Bytes, nome e content-type do arquivo.

        Raises:
            ValidationError: Quando algum id não existe.
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
            list[AtoAdministrativo]: Atos em ordem alfabética de DRE e,
            dentro da DRE, por tipo de ato e número de portaria.

        Raises:
            ValidationError: Quando algum id não existe.

        """
        # Import local para evitar dependência do DRF no módulo inteiro.
        from rest_framework.exceptions import ValidationError

        atos = list(
            AtoAdministrativo.objects.filter(pk__in=ids).select_related(
                "designacao_detalhe__impedimento_substituicao",
                "cessacao_detalhe",
                "apostila_detalhe",
                "ato_pai__ato_pai",
                "ato_raiz__designacao_detalhe__impedimento_substituicao",
            )
        )

        encontrados = {ato.pk for ato in atos}
        faltando = sorted(set(ids) - encontrados)
        if faltando:
            raise ValidationError(
                {"detail": f"Atos não encontrados: {_listar(faltando)}."}
            )

        # TO-DO: confirmar com a área se ato já publicado pode voltar para
        # a lauda (reimpressão/republicação). Por ora não há trava.

        # TO-DO: a ordem vai passar a ser escolhida pelo usuário na tela.
        return sorted(atos, key=_chave_ordenacao)

    @staticmethod
    def montar_documento(atos: list[AtoAdministrativo]) -> DocumentoLauda:
        """Monta a estrutura neutra consumida pelos renderers.

        Args:
            atos: Atos já validados e ordenados.

        Returns:
            DocumentoLauda: Uma seção por ato, na ordem recebida.

        """
        codigos = {
            str(codigo)
            for ato in atos
            for codigo in (
                _codigo_cargo_vaga(_detalhe_designacao(ato)),
                _codigo_cargo_titular(_detalhe_designacao(ato)),
                _codigo_cargo_indicado(_detalhe_designacao(ato)),
            )
            if codigo
        }
        cargos = {
            cargo.codigo_cargo: cargo
            for cargo in CargoBase.objects.filter(codigo_cargo__in=codigos)
        }
        return DocumentoLauda(
            titulo=LaudaService.TITULO,
            secoes=[LaudaService.secao(ato, cargos) for ato in atos],
        )

    @staticmethod
    def secao(
        ato: AtoAdministrativo, cargos: dict[str, CargoBase]
    ) -> SecaoLauda:
        """Monta título, DRE e corpo de um ato.

        Args:
            ato: Ato administrativo (com relacionamentos carregados).
            cargos: Cargos base por código, para o nome e o provimento
                do cargo da designação e para o nome dos cargos do
                indicado e do titular.

        Returns:
            SecaoLauda: Seção pronta para os renderers.

        """
        texto = _TextoAto(ato, cargos)
        titulo, corpo = texto.montar()
        return SecaoLauda(
            titulo=titulo,
            dre=_dre(texto.detalhe.dre_nome),
            corpo=corpo,
        )


class _TextoAto:
    """Monta o texto de publicação de um ato a partir do banco.

    Os dados do servidor, da unidade e do cargo vêm sempre da designação
    raiz — já com as alterações de apostilas aplicadas.
    """

    def __init__(self, ato: AtoAdministrativo, cargos: dict[str, CargoBase]):
        self.ato = ato
        self.designacao = _designacao_ato(ato)
        self.detalhe: DesignacaoDetalhe = self.designacao.designacao_detalhe
        self.cargos = cargos
        cargo = cargos.get(str(_codigo_cargo_vaga(self.detalhe)))
        # Nome oficial do cargo, a mesma fonte do texto SEI. A descrição
        # resumida pode ser sigla (ex.: "CP"). Sem cadastro, usa o nome do
        # EOL do cargo do titular, como o texto SEI.
        self.cargo = (
            cargo.descricao_completa if cargo else self._cargo_titular_eol()
        )
        self.provimento = cargo.provimento.strip().rstrip(".") if cargo else ""
        self._trechos: Linha = []

    def montar(self) -> tuple[str, Linha]:
        tipo = AtoAdministrativo.Tipo
        pai = self.ato.ato_pai
        if self.ato.tipo == tipo.DESIGNACAO:
            self._designando()
            titulo = (
                "SUBSTITUIÇÃO"
                if self.detalhe.impedimento_substituicao
                else "DESIGNANDO"
            )
        elif self.ato.tipo == tipo.APOSTILA:
            self._apostilando()
            titulo = "APOSTILANDO"
        elif self.ato.tipo == tipo.CESSACAO:
            self._fazendo_cessar()
            titulo = "FAZENDO CESSAR"
        elif pai is not None and pai.tipo == tipo.APOSTILA:
            self._tornar_sem_efeito()
            titulo = "TORNAR SEM EFEITO"
        else:
            self._tornando_insubsistente()
            titulo = "TORNANDO INSUBSISTENTE"
        return titulo, self._trechos

    # ── um método por tipo de ato ──

    def _designando(self) -> None:
        d = self.detalhe
        self._cabecalho_portaria()
        self._servidor()
        self._texto(
            f", {SITUACAO_FUNCIONAL}, lotado(a) "
            f"{_na_unidade(d.indicado_lotacao)}, para exercer o cargo de "
            f"{self.cargo}, {self._local_designacao()}, "
            f"EH: {d.codigo_hierarquico}, "
        )
        if self._tem_titular():
            self._texto(
                f"em substituição a {self._titular()}, Registro nº "
                f"{_rf(d.titular_rf)}, Vínculo {d.titular_vinculo}, "
                f"{self._cargo_titular()}, {SITUACAO_FUNCIONAL}, "
            )
            if d.impedimento_substituicao:
                self._texto(f"{_motivo(d)}, ")
        else:
            self._texto(
                f"{d.get_tipo_vaga_display().lower()}, "
                "previsto na Lei 14.660/2007, "
            )
        provimento = f", {self.provimento}" if self.provimento else ""
        self._texto(f"{self._periodo()}{provimento}.")

    def _apostilando(self) -> None:
        d = self.detalhe
        apostilado = self.ato.ato_pai
        assert apostilado is not None
        self._texto(f"a portaria nº {_numero(apostilado)}", negrito=True)
        self._texto(
            f", de S.M.E., D.O.C. de {_data(apostilado.doc)}, SEI nº "
            f"{apostilado.sei_numero}, em nome de "
        )
        self._texto(self._indicado(), negrito=True)
        self._texto(
            f", registro nº {_rf(d.indicado_rf)}, vínculo "
            f"{d.indicado_vinculo}, a fim de declarar "
            f"{_declaracao(self.ato.apostila_detalhe.observacao)} - "
            f"(SEI nº {self.ato.sei_numero})."
        )

    def _tornar_sem_efeito(self) -> None:
        d = self.detalhe
        apostila = self.ato.ato_pai
        assert apostila is not None and apostila.ato_pai is not None
        apostilado = apostila.ato_pai
        self._cabecalho_portaria()
        self._texto(
            f"a Apostila feita na Portaria nº {_numero(apostilado)}, de "
            f"S.M.E., D.O.C. de {_data(apostilado.doc)}, em nome de "
        )
        self._texto(self._indicado(), negrito=True)
        self._texto(
            f", registro nº {_rf(d.indicado_rf)}, vínculo "
            f"{d.indicado_vinculo}, publicada no D.O.C. de "
            f"{_data(apostila.doc)}."
        )

    def _fazendo_cessar(self) -> None:
        d = self.detalhe
        cessacao = self.ato.cessacao_detalhe
        self._cabecalho_portaria()
        self._servidor()
        motivos = [
            texto
            for marcado, texto in (
                (cessacao.a_pedido, "a pedido"),
                (cessacao.remocao, "por remoção"),
                (cessacao.aposentadoria, "por aposentadoria"),
            )
            if marcado
        ]
        self._texto(", " + "".join(f"{m}, " for m in motivos))
        self._texto(
            f"os efeitos da Portaria nº {self.designacao.numero_portaria}, "
            f"{self._referencia(self.designacao)}, pela qual o(a) "
            "servidor(a) foi designado(a) "
        )
        if self._tem_titular():
            self._texto(
                f"para substituir o(a) Sr.(a) {self._titular()}, "
                f"{self._dados_titular()}, "
                f"{_na_unidade(d.unidade_proponente)}"
            )
        else:
            self._texto(
                f"para exercer o cargo de {self.cargo}, "
                f"{_na_unidade(d.unidade_proponente)}"
            )
        self._texto(f", a partir de {_data(cessacao.data_cessacao)}.")

    def _tornando_insubsistente(self) -> None:
        d = self.detalhe
        pai = self.ato.ato_pai
        assert pai is not None
        self._cabecalho_portaria()
        self._servidor()
        self._texto(
            f", os efeitos da Port. {pai.numero_portaria}, "
            f"{self._referencia(pai)}"
        )
        # TO-DO: texto de insubsistência de insubsistência ainda não
        # definido pela área; por ora só referencia a portaria anulada.
        if pai.tipo == AtoAdministrativo.Tipo.INSUBSISTENCIA:
            self._texto(".")
            return

        if pai.tipo == AtoAdministrativo.Tipo.CESSACAO:
            self._texto(
                ", que cessou os efeitos da Port. nº "
                f"{self.designacao.numero_portaria}, "
                f"{self._referencia(self.designacao)}"
            )
        self._texto(", pela qual o(a) servidor(a) foi designado(a) ")
        if self._tem_titular():
            motivo = (
                _motivo(d)
                if d.impedimento_substituicao
                else "durante seu impedimento legal"
            )
            self._texto(
                f"em substituição a {self._titular()}, "
                f"{self._dados_titular()}, "
                f"{_na_unidade(d.unidade_proponente)}, {motivo}, "
            )
        else:
            self._texto(
                f"para exercer o cargo de {self.cargo}, "
                f"{_na_unidade(d.unidade_proponente)}, "
            )
        self._texto(f"{self._periodo()}.")

    # ── trechos reaproveitados ──

    def _texto(self, texto: str, negrito: bool = False) -> None:
        self._trechos.append(Trecho(texto, negrito=negrito))

    def _cabecalho_portaria(self) -> None:
        """``Port. 88000/2026 - SEI nº 6016... -`` em negrito."""
        self._texto(
            f"Port. {_numero(self.ato)} - SEI nº {self.ato.sei_numero} -",
            negrito=True,
        )
        self._texto(" ")

    def _servidor(self) -> None:
        """``RF, Vínculo N - NOME, Cargo``."""
        d = self.detalhe
        self._texto(f"{_rf(d.indicado_rf)}, Vínculo {d.indicado_vinculo} - ")
        self._texto(self._indicado(), negrito=True)
        self._texto(f", {self._cargo_indicado()}")

    def _cargo_indicado(self) -> str:
        """Cargo do indicado, igual ao ``[[CARGO_INDICADO]]`` do texto SEI.

        Regra da PO: com cargo sobreposto, exibe o sobreposto, sem
        categoria. Sem ele, exibe o cargo base e, quando é de professor,
        a categoria logo depois (``- Categoria N``). Função/atividade não
        conta como cargo sobreposto.

        O nome é a descrição completa do cadastro de cargos, pelo código;
        sem cadastro, usa o nome do EOL gravado na designação.
        """
        d = self.detalhe
        cadastro = self.cargos.get(str(_codigo_cargo_indicado(d)))
        sobreposto = (d.indicado_cargo_sobreposto or "").strip()
        if _indicado_tem_sobreposto(d):
            return cadastro.descricao_completa if cadastro else sobreposto

        cargo = (
            cadastro.descricao_completa if cadastro else d.indicado_cargo_base
        )
        if (
            d.indicado_categoria
            and d.indicado_codigo_cargo_base in CODIGOS_CARGO_PROFESSOR
        ):
            return f"{cargo} - Categoria {d.indicado_categoria}"
        return cargo

    @staticmethod
    def _referencia(ato: AtoAdministrativo) -> str:
        return (
            f"de S.M.E., D.O.C. de {_data(ato.doc)}, SEI nº {ato.sei_numero}"
        )

    def _indicado(self) -> str:
        d = self.detalhe
        return d.indicado_nome_civil or d.indicado_nome_servidor

    def _titular(self) -> str:
        d = self.detalhe
        return d.titular_nome_civil or d.titular_nome_servidor

    def _tem_titular(self) -> bool:
        return bool(self._titular())

    def _cargo_titular(self) -> str:
        """Descrição completa do cargo do titular no cadastro de cargos.

        Sem cadastro para o código, usa o nome do EOL gravado na designação.
        """
        cargo = self.cargos.get(str(_codigo_cargo_titular(self.detalhe)))
        return cargo.descricao_completa if cargo else self._cargo_titular_eol()

    def _cargo_titular_eol(self) -> str:
        d = self.detalhe
        return d.titular_cargo_sobreposto or d.titular_cargo_base

    def _dados_titular(self) -> str:
        d = self.detalhe
        return (
            f"{self._cargo_titular()}, registro nº {_rf(d.titular_rf)}, "
            f"vínculo {d.titular_vinculo}"
        )

    def _local_designacao(self) -> str:
        """``na referida Unidade`` quando o cargo base do indicado é nela.

        A frase imprime ``lotado(a) no {indicado_lotacao}``, que é a UE do
        cargo base, então a comparação usa a mesma UE, e não a do cargo
        sobreposto. Caso contrário, imprime o nome da unidade.

        Sem nenhum código de UE do indicado gravado, compara o nome da
        lotação com o da unidade, ignorando espaços e maiúsculas.
        """
        d = self.detalhe
        lotacao = self._codigo_ue_cargo_base()
        if lotacao:
            mesma_unidade = lotacao == _codigo_ue(d.ue)
        elif self._sem_codigo_ue_do_indicado():
            mesma_unidade = bool(_nome_unidade(d.indicado_lotacao)) and (
                _nome_unidade(d.indicado_lotacao).casefold()
                == _nome_unidade(d.unidade_proponente).casefold()
            )
        else:
            mesma_unidade = False
        if mesma_unidade:
            return "na referida Unidade"
        return _na_unidade(d.unidade_proponente)

    def _sem_codigo_ue_do_indicado(self) -> bool:
        d = self.detalhe
        return not (
            d.indicado_codigo_ue_cargo_base.strip()
            or d.indicado_codigo_ue_lotacao.strip()
        )

    def _codigo_ue_cargo_base(self) -> str:
        """Código da UE do cargo base do indicado, sem zeros à esquerda.

        Designações anteriores a ``indicado_codigo_ue_cargo_base`` só têm
        ``indicado_codigo_ue_lotacao``, que é a UE do cargo base apenas
        quando não há cargo sobreposto. Com sobreposto, não há como saber
        a UE do cargo base e o retorno é vazio.
        """
        d = self.detalhe
        if d.indicado_codigo_ue_cargo_base:
            return _codigo_ue(d.indicado_codigo_ue_cargo_base)
        if d.indicado_possui_cargo_sobreposto:
            return ""
        return _codigo_ue(d.indicado_codigo_ue_lotacao)

    def _periodo(self) -> str:
        d = self.detalhe
        if d.data_fim:
            return (
                f"no período de {_data(d.data_inicio)} a {_data(d.data_fim)}"
            )
        return f"a partir de {_data(d.data_inicio)}"


def _designacao_ato(ato: AtoAdministrativo) -> AtoAdministrativo:
    """Designação de origem do ato (ele mesmo, se for uma designação)."""
    if ato.tipo == AtoAdministrativo.Tipo.DESIGNACAO:
        return ato
    assert ato.ato_raiz is not None
    return ato.ato_raiz


def _detalhe_designacao(ato: AtoAdministrativo) -> DesignacaoDetalhe:
    return _designacao_ato(ato).designacao_detalhe


def _chave_ordenacao(ato: AtoAdministrativo) -> tuple:
    """DRE (alfabética) → tipo de ato → nº de portaria → id."""
    return (
        _dre(_detalhe_designacao(ato).dre_nome).casefold(),
        _ORDEM_TIPOS.index(ato.tipo),
        ato.numero_portaria is None,
        ato.numero_portaria or 0,
        ato.pk,
    )


def _dre(dre_nome: str) -> str:
    """``DRE BUTANTA`` → ``Diretoria Regional de Educação BUTANTA``."""
    nome = dre_nome.strip()
    for prefixo in _PREFIXOS_DRE:
        if nome.upper().startswith(prefixo):
            nome = nome[len(prefixo) :].strip(" -")
            break
    return f"Diretoria Regional de Educação {nome}"


def _codigo_ue(codigo: str) -> str:
    """Ignora zeros à esquerda: o EOL devolve ``90450`` ou ``090450``."""
    return codigo.strip().lstrip("0")


def _nome_unidade(unidade: str) -> str:
    """Nome da unidade sem espaços repetidos (``CEI DIRET    - X``)."""
    return " ".join(unidade.split())


def _na_unidade(unidade: str) -> str:
    """Prefixa a unidade com ``na``/``no`` conforme o tipo da unidade."""
    unidade = _nome_unidade(unidade)
    tipo = unidade.split(maxsplit=1)[0].upper() if unidade else ""
    preposicao = "na" if tipo in _UNIDADES_FEMININAS else "no"
    return f"{preposicao} {unidade}"


def _codigo_cargo_titular(detalhe: DesignacaoDetalhe) -> int | None:
    """Código do cargo do titular: o sobreposto, se houver; senão o base.

    Segue a mesma escolha do nome do cargo do titular, que usa o
    sobreposto quando ele está preenchido.
    """
    if (
        detalhe.titular_cargo_sobreposto.strip()
        and detalhe.titular_codigo_cargo_sobreposto
    ):
        return detalhe.titular_codigo_cargo_sobreposto
    return detalhe.titular_codigo_cargo_base or None


def _indicado_tem_sobreposto(detalhe: DesignacaoDetalhe) -> bool:
    """Cargo sobreposto de fato (função/atividade não conta)."""
    return detalhe.indicado_possui_cargo_sobreposto and bool(
        (detalhe.indicado_cargo_sobreposto or "").strip()
    )


def _codigo_cargo_indicado(detalhe: DesignacaoDetalhe) -> int | None:
    """Código do cargo exibido do indicado: o sobreposto ou o base."""
    if _indicado_tem_sobreposto(detalhe):
        return detalhe.indicado_codigo_cargo_sobreposto or None
    return detalhe.indicado_codigo_cargo_base or None


def _codigo_cargo_vaga(detalhe: DesignacaoDetalhe) -> int | None:
    """Código do cargo a ser ocupado.

    É ``cargo_vaga``. Designações de cargo disponível sem esse código
    ocupam o cargo do titular.
    """
    if detalhe.cargo_vaga is not None:
        return detalhe.cargo_vaga
    return _codigo_cargo_titular(detalhe)


def _motivo(detalhe: DesignacaoDetalhe) -> str:
    """``Por férias`` → ``por férias``."""
    assert detalhe.impedimento_substituicao is not None
    descricao = detalhe.impedimento_substituicao.descricao
    return descricao[:1].lower() + descricao[1:]


def _declaracao(observacao: str) -> str:
    """Texto digitado na apostila, sem repetir ``a fim de declarar``."""
    texto = observacao.strip().rstrip(".").strip()
    prefixo = "a fim de declarar"
    if texto.lower().startswith(prefixo):
        texto = texto[len(prefixo) :].strip()
    return texto


def _numero(ato: AtoAdministrativo) -> str:
    """``88000/2026`` (ou só o número, quando não há ano)."""
    if ato.ano_vigente:
        return f"{ato.numero_portaria}/{ato.ano_vigente}"
    return str(ato.numero_portaria)


def _rf(rf: str) -> str:
    """``7255667`` → ``725.566.7``; outros formatos ficam como vieram."""
    if len(rf) == 7 and rf.isdecimal():
        return f"{rf[:3]}.{rf[3:6]}.{rf[6]}"
    return rf


def _data(data: datetime.date | None) -> str:
    return f"{data:%d/%m/%Y}" if data else _DATA_VAZIA


def _listar(ids: list[int]) -> str:
    return ", ".join(str(i) for i in ids)
