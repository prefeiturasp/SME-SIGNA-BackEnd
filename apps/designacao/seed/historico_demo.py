"""Dados de demonstração do histórico de designações.

Cria, em quatro unidades escolares, designações, cessações, apostilas e
insubsistências cobrindo todos os tipos de ato, todas as combinações de
hierarquia aceitas por ``AtoAdministrativo.TIPOS_PAI_VALIDOS`` e as
situações que o endpoint ``/historico-de-designacoes/<codigo_ue>/``
precisa exibir:

- designação vigente, cessada e com ``data_fim`` no passado;
- cessação ativa, cessação tornada sem efeito e designação com duas
  cessações (uma inválida e uma válida);
- apostila sobre designação e apostila sobre cessação;
- insubsistência sobre designação, sobre cessação, sobre apostila
  ("Anulação de Apostila") e sobre insubsistência ("Tornar sem efeito");
- atos publicados (``doc`` preenchido) e não publicados;
- observações com o texto ``ssss`` para exercitar o filtro
  ``?observacao=ssss``.

Todos os atos usam o prefixo ``DEMO-`` em ``sei_numero``: é o marcador
que permite apagar somente os dados de demonstração, sem tocar nos
cadastros reais.
"""

import datetime
from typing import Any

from django.db import transaction
from django.db.models import QuerySet

from apps.designacao.models.apostila_detalhe import (
    ApostilaAlteracao,
    ApostilaDetalhe,
)
from apps.designacao.models.ato_administrativo import AtoAdministrativo
from apps.designacao.models.cessacao_detalhe import CessacaoDetalhe
from apps.designacao.models.designacao import ImpedimentoSubstituicao
from apps.designacao.models.designacao_detalhe import DesignacaoDetalhe
from apps.designacao.models.insubsistencia_apostila_detalhe import (
    InsubsistenciaApostilaDetalhe,
)
from apps.designacao.models.insubsistencia_detalhe import InsubsistenciaDetalhe

# Prefixo de `sei_numero` que identifica os atos de demonstração.
MARCADOR = "DEMO-"

# Variável de ambiente que liga o seed na migração 0027. Sem ela a
# migração não cria nada (assim a suíte de testes não é afetada).
VARIAVEL_AMBIENTE = "SEED_HISTORICO_DESIGNACOES"

# Unidades usadas nos cenários. O `codigo_hierarquico` é igual ao código
# da UE para simplificar a leitura na tela.
UNIDADES: dict[str, dict[str, str]] = {
    "000108": {
        "dre": "DRE Butantã",
        "dre_nome": "Diretoria Regional de Educação Butantã",
        "unidade_proponente": "EMEF Paulo Freire",
    },
    "019453": {
        "dre": "DRE Santo Amaro",
        "dre_nome": "Diretoria Regional de Educação Santo Amaro",
        "unidade_proponente": "EMEF Monteiro Lobato",
    },
    "093712": {
        "dre": "DRE Penha",
        "dre_nome": "Diretoria Regional de Educação Penha",
        "unidade_proponente": "EE Machado de Assis",
    },
    "095432": {
        "dre": "DRE Campo Limpo",
        "dre_nome": "Diretoria Regional de Educação Campo Limpo",
        "unidade_proponente": "EMEF Cecília Meireles",
    },
}

_ANO = "2026"

_TEXTO_PORTARIA = (
    "PORTARIA Nº {numero}/{ano}. O Diretor Regional de Educação, no uso "
    "de suas atribuições legais, resolve: Designar, nos termos da "
    "legislação em vigor, o servidor abaixo relacionado para exercer "
    "suas funções na unidade indicada, ficando revogadas as disposições "
    "em contrário."
)

_TEXTO_APOSTILA = (
    "PORTARIA Nº {numero}/{ano}. Fica apostilada a portaria anterior "
    "para retificar os dados do servidor, mantidas as demais cláusulas."
)

_TEXTO_INSUBSISTENCIA = (
    "PORTARIA Nº {numero}/{ano}. Fica tornada sem efeito a portaria "
    "anterior, por decisão administrativa devidamente fundamentada nos "
    "autos do processo."
)


# ── Helpers de criação ───────────────────────────────────────────────────────


def _texto(modelo: str, numero: int | None) -> str:
    """Monta o texto SEI de um ato de demonstração."""
    if numero is None:
        return ""
    return modelo.format(numero=numero, ano=_ANO)


def _criar_ato(
    *,
    tipo: str,
    chave: str,
    portaria: int | None = None,
    publicado: bool = False,
    doc: datetime.date | None = None,
    pai: AtoAdministrativo | None = None,
    texto: str = "",
) -> AtoAdministrativo:
    """Cria um ato administrativo já validado pelo model.

    Args:
        tipo: Tipo do ato (``AtoAdministrativo.Tipo``).
        chave: Sufixo do ``sei_numero`` (recebe o prefixo ``DEMO-``).
        portaria: Número da portaria.
        publicado: Se o ato já está publicado no Diário Oficial.
        doc: Data de publicação (``doc``).
        pai: Ato pai (None para designação).
        texto: Texto SEI congelado do ato.

    Returns:
        AtoAdministrativo: Ato criado.

    """
    ato = AtoAdministrativo(
        tipo=tipo,
        numero_portaria=portaria,
        ano_vigente=_ANO,
        sei_numero=f"{MARCADOR}{chave}",
        doc=doc,
        ato_pai=pai,
        status_publicacao=(
            AtoAdministrativo.StatusPublicacao.PUBLICADO
            if publicado
            else AtoAdministrativo.StatusPublicacao.NAO_PUBLICADO
        ),
        texto_sei=texto or _texto(_TEXTO_PORTARIA, portaria),
    )
    # `save()` aplica `ato_raiz` e roda `full_clean()` (hierarquia e
    # unicidade de cessação ativa), então os cenários inválidos falham
    # aqui em vez de gerar dados inconsistentes.
    ato.save()
    return ato


def _designacao(
    ue: str,
    chave: str,
    *,
    portaria: int,
    data_inicio: datetime.date,
    data_fim: datetime.date | None = None,
    publicado: bool = False,
    doc: datetime.date | None = None,
    indicado: str = "Maria Aparecida Souza",
    rf: str = "1234567",
    cargo: str = "Professor de Educação Básica II",
    cargo_codigo: int = 3085,
    sobreposto: str = "",
    impedimento: ImpedimentoSubstituicao | None = None,
    **detalhe_extra: Any,
) -> AtoAdministrativo:
    """Cria uma designação com o detalhe completo."""
    ato = _criar_ato(
        tipo=AtoAdministrativo.Tipo.DESIGNACAO,
        chave=chave,
        portaria=portaria,
        publicado=publicado,
        doc=doc,
    )
    unidade = UNIDADES[ue]
    DesignacaoDetalhe.objects.create(
        ato=ato,
        ue=ue,
        dre=unidade["dre"],
        dre_nome=unidade["dre_nome"],
        unidade_proponente=unidade["unidade_proponente"],
        codigo_hierarquico=ue,
        funcionarios_da_unidade="12",
        indicado_nome_servidor=indicado,
        indicado_nome_civil=indicado,
        indicado_rf=rf,
        indicado_vinculo=1,
        indicado_cargo_base=cargo,
        indicado_codigo_cargo_base=cargo_codigo,
        indicado_cargo_sobreposto=sobreposto,
        indicado_lotacao=unidade["unidade_proponente"],
        indicado_local_exercicio=unidade["unidade_proponente"],
        indicado_local_servico="Secretaria",
        titular_nome_servidor="João Batista Lima",
        titular_nome_civil="João Batista Lima",
        titular_rf="7654321",
        titular_vinculo=1,
        titular_cargo_base="Diretor de Escola",
        titular_codigo_cargo_base=3360,
        titular_lotacao=unidade["unidade_proponente"],
        data_inicio=data_inicio,
        data_fim=data_fim,
        tipo_vaga=DesignacaoDetalhe.TipoVaga.VAGO,
        cargo_vaga=cargo_codigo,
        impedimento_substituicao=impedimento,
        **detalhe_extra,
    )
    return ato


def _cessacao(
    pai: AtoAdministrativo,
    chave: str,
    *,
    portaria: int,
    data_cessacao: datetime.date,
    publicado: bool = False,
    doc: datetime.date | None = None,
    a_pedido: bool = False,
    remocao: bool = False,
    aposentadoria: bool = False,
) -> AtoAdministrativo:
    """Cria uma cessação vinculada a uma designação."""
    ato = _criar_ato(
        tipo=AtoAdministrativo.Tipo.CESSACAO,
        chave=chave,
        portaria=portaria,
        publicado=publicado,
        doc=doc,
        pai=pai,
    )
    CessacaoDetalhe.objects.create(
        ato=ato,
        a_pedido=a_pedido,
        remocao=remocao,
        aposentadoria=aposentadoria,
        data_cessacao=data_cessacao,
    )
    return ato


def _apostila(
    pai: AtoAdministrativo,
    chave: str,
    *,
    observacao: str,
    portaria: int | None = None,
    publicado: bool = False,
    doc: datetime.date | None = None,
    alteracoes: list[tuple[str, str, str]] | None = None,
) -> AtoAdministrativo:
    """Cria uma apostila (sobre designação ou sobre cessação).

    Args:
        pai: Ato apostilado.
        chave: Sufixo do ``sei_numero``.
        observacao: Texto da observação da apostila.
        portaria: Número da portaria (None exercita ``portaria=null``).
        publicado: Se a apostila já foi publicada.
        doc: Data de publicação.
        alteracoes: Lista de ``(campo, valor_anterior, valor_novo)``
            registradas em ``ApostilaAlteracao``.

    Returns:
        AtoAdministrativo: Apostila criada.

    """
    ato = _criar_ato(
        tipo=AtoAdministrativo.Tipo.APOSTILA,
        chave=chave,
        portaria=portaria,
        publicado=publicado,
        doc=doc,
        pai=pai,
        texto=_texto(_TEXTO_APOSTILA, portaria),
    )
    detalhe = ApostilaDetalhe.objects.create(ato=ato, observacao=observacao)
    for campo, anterior, novo in alteracoes or []:
        ApostilaAlteracao.objects.create(
            apostila=detalhe,
            ato_alterado=pai,
            campo_alterado=campo,
            valor_anterior=anterior,
            valor_novo=novo,
        )
    return ato


def _insubsistencia(
    pai: AtoAdministrativo,
    chave: str,
    *,
    portaria: int,
    observacoes: str,
    texto_apostila: str = "",
    publicado: bool = False,
    doc: datetime.date | None = None,
) -> AtoAdministrativo:
    """Cria uma insubsistência sobre o ato pai informado.

    Aceita qualquer tipo de ato pai permitido por
    ``AtoAdministrativo.TIPOS_PAI_VALIDOS`` (inclusive designação).
    """
    ato = _criar_ato(
        tipo=AtoAdministrativo.Tipo.INSUBSISTENCIA,
        chave=chave,
        portaria=portaria,
        publicado=publicado,
        doc=doc,
        pai=pai,
        texto=_texto(_TEXTO_INSUBSISTENCIA, portaria),
    )
    InsubsistenciaDetalhe.objects.create(ato=ato, observacoes=observacoes)
    if pai.tipo == AtoAdministrativo.Tipo.APOSTILA:
        InsubsistenciaApostilaDetalhe.objects.create(
            ato=ato, texto=texto_apostila or observacoes
        )
    return ato


def _desativar(ato: AtoAdministrativo) -> None:
    """Marca o ato como insubsistente sem revalidar o model.

    ``update_fields`` faz o ``save()`` pular o ``full_clean()``, que
    recusaria duas cessações ativas no mesmo pai durante a montagem do
    cenário.
    """
    ato.ativo = False
    ato.save(update_fields=["ativo"])


def _reativar(ato: AtoAdministrativo) -> None:
    """Devolve o ato à condição de válido (tornar sem efeito)."""
    ato.ativo = True
    ato.save(update_fields=["ativo"])


def _impedimento() -> ImpedimentoSubstituicao | None:
    """Retorna um impedimento cadastrado, se existir."""
    return ImpedimentoSubstituicao.objects.filter(codigo="LIC_MEDICA").first()


# ── Cenários por unidade escolar ────────────────────────────────────────────


def _ue_000108() -> None:
    """Árvore de 4 níveis: designação → cessação → apostila → anulação.

    Também concentra as variações de período (inclusive a janela
    ``2026-10-06`` a ``2026-11-10`` usada nos testes manuais do filtro).
    """
    impedimento = _impedimento()

    # D1 cessada, com árvore completa até o 4º nível.
    d1 = _designacao(
        "000108",
        "108-D1",
        portaria=101,
        data_inicio=datetime.date(2026, 1, 15),
        data_fim=datetime.date(2026, 12, 31),
        publicado=True,
        doc=datetime.date(2026, 1, 10),
        indicado="Ana Paula Ribeiro",
        rf="1111111",
        impedimento=impedimento,
    )
    c1 = _cessacao(
        d1,
        "108-C1",
        portaria=102,
        data_cessacao=datetime.date(2026, 2, 1),
        publicado=True,
        doc=datetime.date(2026, 2, 1),
        a_pedido=True,
    )
    a1 = _apostila(
        c1,
        "108-A1",
        observacao="Retifica o motivo informado na cessação.",
        portaria=None,  # exercita portaria = null
        publicado=True,
        doc=datetime.date(2026, 2, 10),
    )
    _insubsistencia(
        a1,
        "108-I1",
        portaria=103,
        observacoes="ssss - anula a apostila por erro material.",
        texto_apostila="Fica anulada a apostila por erro material.",
        publicado=True,
        doc=datetime.date(2026, 2, 20),
    )
    _desativar(a1)

    # D2 vigente, ainda não publicada, sem nenhum ato derivado.
    _designacao(
        "000108",
        "108-D2",
        portaria=104,
        data_inicio=datetime.date(2026, 3, 1),
        indicado="Carlos Eduardo Nunes",
        rf="2222222",
    )

    # D3 com data_fim no passado: não está vigente pela regra de data.
    _designacao(
        "000108",
        "108-D3",
        portaria=105,
        data_inicio=datetime.date(2025, 2, 1),
        data_fim=datetime.date(2025, 12, 31),
        publicado=True,
        doc=datetime.date(2025, 2, 1),
        indicado="Fernanda Dias Castro",
        rf="3333333",
    )

    # D4 vigente com apostila sobre a própria designação (tem alterações).
    d4 = _designacao(
        "000108",
        "108-D4",
        portaria=106,
        data_inicio=datetime.date(2026, 4, 1),
        publicado=True,
        doc=datetime.date(2026, 4, 1),
        indicado="Marcos Vinícius Alves",
        rf="4444444",
        com_afastamento=True,
        motivo_afastamento="Licença médica do titular.",
        informacoes_adicionais="Designação para substituição durante o "
        "afastamento do titular.",
    )
    _apostila(
        d4,
        "108-A2",
        observacao="ssss - altera o nome e a RF do servidor indicado.",
        portaria=107,
        publicado=True,
        doc=datetime.date(2026, 4, 15),
        alteracoes=[
            (
                "indicado_nome_servidor",
                "Marcos Vinícius Alves",
                "Marcos Vinícius Alves Junior",
            ),
            ("indicado_rf", "4444444", "4444445"),
        ],
    )

    # D5 dentro da janela de 2026-10-06 a 2026-11-10, não publicada e com
    # observação "ssss": é a designação devolvida pela URL usada nos
    # testes manuais (status_publicacao=NAO_PUBLICADO + periodo + observacao).
    d5 = _designacao(
        "000108",
        "108-D5",
        portaria=108,
        data_inicio=datetime.date(2026, 10, 20),
        indicado="Patrícia Gomes Ferreira",
        rf="5555555",
    )
    _apostila(
        d5,
        "108-A3",
        observacao="ssss - ajuste de carga horária autorizado.",
        portaria=109,
        doc=None,
    )


def _ue_019453() -> None:
    """Cessações: tornar sem efeito, duas cessações e designação desfeita."""
    # D6: cessação ativa e depois tornada sem efeito (designação volta a
    # ficar vigente).
    d6 = _designacao(
        "019453",
        "453-D6",
        portaria=201,
        data_inicio=datetime.date(2026, 1, 5),
        publicado=True,
        doc=datetime.date(2026, 1, 5),
        indicado="Roberto Carlos Mendes",
        rf="6666666",
        sobreposto="Coordenador Pedagógico",
        cargo_codigo=3379,
    )
    c2 = _cessacao(
        d6,
        "453-C2",
        portaria=202,
        data_cessacao=datetime.date(2026, 3, 10),
        publicado=True,
        doc=datetime.date(2026, 3, 10),
        remocao=True,
    )
    i2 = _insubsistencia(
        c2,
        "453-I2",
        portaria=203,
        observacoes="ssss - torna sem efeito a cessação.",
        publicado=True,
        doc=datetime.date(2026, 3, 20),
    )
    _desativar(c2)
    assert i2.ativo

    # D7: duas cessações — a primeira tornada sem efeito, a segunda
    # válida. `cessada_em` deve trazer a data da cessação válida.
    d7 = _designacao(
        "019453",
        "453-D7",
        portaria=204,
        data_inicio=datetime.date(2026, 2, 1),
        publicado=True,
        doc=datetime.date(2026, 2, 1),
        indicado="Sandra Regina Melo",
        rf="7777777",
    )
    c3 = _cessacao(
        d7,
        "453-C3",
        portaria=205,
        data_cessacao=datetime.date(2026, 4, 1),
        publicado=True,
        doc=datetime.date(2026, 4, 1),
        aposentadoria=True,
    )
    _insubsistencia(
        c3,
        "453-I3",
        portaria=206,
        observacoes="ssss - cessação indevida, tornada sem efeito.",
        publicado=True,
        doc=datetime.date(2026, 4, 10),
    )
    _desativar(c3)
    _cessacao(
        d7,
        "453-C4",
        portaria=207,
        data_cessacao=datetime.date(2026, 6, 1),
        publicado=True,
        doc=datetime.date(2026, 6, 1),
        a_pedido=True,
    )

    # D8: insubsistência direta da designação (ato de designação fica
    # insubsistente, sem cessação).
    d8 = _designacao(
        "019453",
        "453-D8",
        portaria=208,
        data_inicio=datetime.date(2026, 5, 1),
        publicado=True,
        doc=datetime.date(2026, 5, 1),
        indicado="Luciana Prado Rocha",
        rf="8888888",
    )
    i4 = _insubsistencia(
        d8,
        "453-I4",
        portaria=209,
        observacoes="ssss - designação tornada sem efeito.",
        publicado=True,
        doc=datetime.date(2026, 5, 15),
    )
    _desativar(d8)
    assert i4.ativo


def _ue_093712() -> None:
    """Apostilas e insubsistências em cadeia (4 níveis no segundo ramo)."""
    # D9: apostila anulada e anulação tornada sem efeito — a apostila
    # volta a valer.
    d9 = _designacao(
        "093712",
        "712-D9",
        portaria=301,
        data_inicio=datetime.date(2026, 1, 20),
        publicado=True,
        doc=datetime.date(2026, 1, 20),
        indicado="Eduardo Tavares Pinto",
        rf="9999999",
        informacoes_adicionais="Designação em caráter excepcional.",
    )
    a4 = _apostila(
        d9,
        "712-A4",
        observacao="ssss - altera a lotação do servidor indicado.",
        portaria=302,
        publicado=True,
        doc=datetime.date(2026, 1, 25),
        alteracoes=[
            (
                "indicado_lotacao",
                "EMEF Monteiro Lobato",
                "EE Machado de Assis",
            )
        ],
    )
    i5 = _insubsistencia(
        a4,
        "712-I5",
        portaria=303,
        observacoes="ssss - anula a apostila anterior.",
        texto_apostila="Fica anulada a apostila anterior.",
        publicado=True,
        doc=datetime.date(2026, 2, 1),
    )
    _desativar(a4)
    _insubsistencia(
        i5,
        "712-I6",
        portaria=304,
        observacoes="ssss - torna sem efeito a anulação da apostila.",
        publicado=True,
        doc=datetime.date(2026, 2, 10),
    )
    # "Tornar sem efeito" restaura o ato original (mesma regra do
    # InsubsistenciaService.criar).
    _desativar(i5)
    _reativar(a4)

    # D10: cessação ativa + apostila sobre a cessação + apostila sobre a
    # designação, misturando atos publicados e não publicados.
    d10 = _designacao(
        "093712",
        "712-D10",
        portaria=305,
        data_inicio=datetime.date(2026, 2, 10),
        publicado=True,
        doc=datetime.date(2026, 2, 10),
        indicado="Beatriz Almeida Cardoso",
        rf="1010101",
        carater_excepcional=True,
    )
    c5 = _cessacao(
        d10,
        "712-C5",
        portaria=306,
        data_cessacao=datetime.date(2026, 5, 2),
        publicado=True,
        doc=datetime.date(2026, 5, 2),
        remocao=True,
    )
    _apostila(
        c5,
        "712-A5",
        observacao="ssss - retifica a data de cessação.",
        portaria=307,
        publicado=True,
        doc=datetime.date(2026, 5, 5),
        alteracoes=[
            ("data_cessacao", "2026-05-02", "2026-05-20"),
        ],
    )
    _apostila(
        d10,
        "712-A6",
        observacao="Altera o local de exercício do servidor.",
        portaria=308,
    )


def _ue_095432() -> None:
    """Status de publicação variados e atos sem portaria."""
    # D11: rascunho (não publicado, sem doc) e vigente.
    _designacao(
        "095432",
        "432-D11",
        portaria=401,
        data_inicio=datetime.date(2026, 6, 1),
        indicado="Gustavo Henrique Barros",
        rf="1212121",
        possui_pendencia=True,
        pendencias="Aguardando documentação do servidor.",
    )

    # D12: cessação ativa, mas ainda não publicada.
    d12 = _designacao(
        "095432",
        "432-D12",
        portaria=402,
        data_inicio=datetime.date(2026, 6, 15),
        publicado=True,
        doc=datetime.date(2026, 6, 15),
        indicado="Helena Martins Vieira",
        rf="1313131",
    )
    _cessacao(
        d12,
        "432-C6",
        portaria=403,
        data_cessacao=datetime.date(2026, 9, 1),
        aposentadoria=True,
    )

    # D13: publicada, com apostila não publicada e insubsistência ativa
    # (designação fica insubsistente).
    d13 = _designacao(
        "095432",
        "432-D13",
        portaria=404,
        data_inicio=datetime.date(2026, 7, 1),
        publicado=True,
        doc=datetime.date(2026, 7, 1),
        indicado="Igor Fernandes Prado",
        rf="1414141",
        com_afastamento=True,
        motivo_afastamento="Afastamento por licença médica.",
    )
    _apostila(
        d13,
        "432-A7",
        observacao="ssss - pendência sanada após reanálise.",
        portaria=405,
    )
    i7 = _insubsistencia(
        d13,
        "432-I7",
        portaria=406,
        observacoes="ssss - designação tornada sem efeito por decisão "
        "judicial.",
        publicado=True,
        doc=datetime.date(2026, 8, 1),
    )
    _desativar(d13)
    assert i7.ativo

    # D14: designação com impedimento de substituição e data_fim futura.
    _designacao(
        "095432",
        "432-D14",
        portaria=407,
        data_inicio=datetime.date(2026, 8, 1),
        data_fim=datetime.date(2028, 12, 31),
        publicado=True,
        doc=datetime.date(2026, 8, 1),
        indicado="Juliana Costa Ramos",
        rf="1515151",
        sobreposto="Assistente de Diretor de Escola",
        cargo_codigo=3085,
        impedimento=_impedimento(),
    )


# ── API pública ─────────────────────────────────────────────────────────────


def _todos_demo() -> QuerySet[AtoAdministrativo]:
    """Queryset com todos os atos de demonstração."""
    return AtoAdministrativo.objects.filter(sei_numero__startswith=MARCADOR)


def apagar_dados_demo() -> int:
    """Remove os atos de demonstração (e seus detalhes).

    Os atos são apagados das folhas para as raízes, porque ``ato_pai``
    usa ``PROTECT`` e não permite apagar um pai com filhos.

    Returns:
        int: Quantidade de atos removidos.

    """
    atos = list(_todos_demo().order_by("pk"))
    if not atos:
        return 0

    removidos = 0

    while atos:
        # Recalculado a cada rodada: um pai só é folha depois que todos
        # os filhos dele já foram removidos.
        pks_com_filhos = {ato.ato_pai_id for ato in atos if ato.ato_pai_id}
        folhas = [ato for ato in atos if ato.pk not in pks_com_filhos]
        if not folhas:
            break  # não deveria acontecer (a hierarquia é uma árvore)

        pks_removidos = set()
        for ato in folhas:
            ato.delete()
            pks_removidos.add(ato.pk)

        removidos += len(folhas)
        atos = [ato for ato in atos if ato.pk not in pks_removidos]

    return removidos


def resumo() -> dict[str, Any]:
    """Retorna as quantidades de atos de demonstração por tipo e por UE.

    Returns:
        dict[str, Any]: ``{"total": int, "por_tipo": {...}, "por_ue": {...}}``.

    """
    por_tipo = {
        tipo.value: _todos_demo().filter(tipo=tipo.value).count()
        for tipo in AtoAdministrativo.Tipo
    }
    por_ue = {
        ue: _todos_demo()
        .filter(
            tipo=AtoAdministrativo.Tipo.DESIGNACAO,
            designacao_detalhe__ue=ue,
        )
        .count()
        for ue in UNIDADES
    }
    return {
        "total": _todos_demo().count(),
        "por_tipo": por_tipo,
        "por_ue": por_ue,
    }


def criar_dados_demo() -> dict[str, Any]:
    """Recria os dados de demonstração nas quatro UEs.

    Idempotente: apaga os dados de demonstração anteriores e cria tudo
    novamente, sem tocar em designações reais.

    Returns:
        dict[str, Any]: Resumo de :func:`resumo` após a criação.

    """
    with transaction.atomic():
        apagar_dados_demo()

        _ue_000108()
        _ue_019453()
        _ue_093712()
        _ue_095432()

        return resumo()


def dados_existem() -> bool:
    """Indica se já existem dados de demonstração no banco."""
    return _todos_demo().exists()
