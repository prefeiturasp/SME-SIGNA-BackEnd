"""Serializadores do histórico de designações por unidade escolar.

O payload segue a nomenclatura já usada nas outras telas do sistema:

* **campos de ato** iguais aos de ``AtoAdministrativoListSerializer`` /
  ``PortariaListSerializer``: ``tipo_de_ato``, ``status``,
  ``status_publicacao``, ``numero_portaria``, ``ano_vigente``,
  ``sei_numero``, ``doc``, ``nome``, ``cargo``, ``rf``, ``observacoes``,
  ``tipo_insubsistencia``, ``tipo_apostila``, ``ato_pai_id``,
  ``criado_em``, ``criado_por_nome``;
* **campos de detalhe da designação** iguais aos de
  ``DesignacaoReadSerializer``: ``indicado_*``, ``titular_*``,
  ``data_inicio``, ``data_fim``, flags, ``impedimento_*``,
  ``tipo_vaga``/``cargo_vaga`` e os respectivos displays.

Somam-se a esses somente os campos próprios do histórico: ``vigente``,
``cessada_em``, ``atos_relacionados``, ``nivel``, ``ultimo_ato_vigente``
e ``portaria`` (número/ano já formatado, como usado no front).
"""

import datetime
from typing import Any, cast

from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import extend_schema_field
from rest_framework import serializers

from apps.designacao.api.serializers.ato_relacionado_mixin import (
    AtoRelacionadoMixin,
)
from apps.designacao.api.serializers.designacao_serializer import (
    ImpedimentoSubstituicaoSerializer,
)
from apps.designacao.models.ato_administrativo import AtoAdministrativo

# Nomes compartilhados pelos três payloads. A ordem de cada tupla é a ordem
# do JSON; os campos simples do detalhe são declarados a partir dela, sem
# repetir `source="designacao_detalhe.<campo>"` em cada atributo.
_CAMPOS_ATO_INICIO = (
    "id",
    "tipo",
    "tipo_de_ato",
    "status",
    "status_publicacao",
)
_CAMPOS_PORTARIA = (
    "numero_portaria",
    "ano_vigente",
    "sei_numero",
    "doc",
    "portaria",
)
_CAMPOS_SERVIDOR = ("nome", "cargo", "rf")
_CAMPOS_ATO_FIM = (
    "ato_pai_id",
    "ato_raiz_id",
    "criado_em",
    "criado_por_nome",
)
_CAMPOS_ATO = (
    *_CAMPOS_ATO_INICIO,
    *_CAMPOS_PORTARIA,
    *_CAMPOS_SERVIDOR,
    *_CAMPOS_ATO_FIM,
)
_CAMPOS_ATO_RELACIONADO = (
    *_CAMPOS_ATO_INICIO,
    "ativo",
    *_CAMPOS_PORTARIA,
    "data_designacao",
    "data_cessacao",
    *_CAMPOS_SERVIDOR,
    "observacoes",
    "tipo_insubsistencia",
    "tipo_apostila",
    *_CAMPOS_ATO_FIM,
    "nivel",
    "ultimo_ato_vigente",
)
_DETALHE_UNIDADE = (
    "ue",
    "dre",
    "dre_nome",
    "unidade_proponente",
    "codigo_hierarquico",
    "funcionarios_da_unidade",
)
_DETALHE_INDICADO = (
    "indicado_nome_civil",
    "indicado_nome_servidor",
    "indicado_rf",
    "indicado_vinculo",
    "indicado_cargo_base",
    "indicado_codigo_cargo_base",
    "indicado_lotacao",
    "indicado_cargo_sobreposto",
    "indicado_codigo_cargo_sobreposto",
    "indicado_local_exercicio",
    "indicado_local_servico",
    "indicado_categoria",
    "indicado_codigo_ue_lotacao",
    "indicado_possui_cargo_sobreposto",
)
_DETALHE_TITULAR = (
    "titular_nome_civil",
    "titular_nome_servidor",
    "titular_rf",
    "titular_vinculo",
    "titular_cargo_base",
    "titular_codigo_cargo_base",
    "titular_lotacao",
    "titular_cargo_sobreposto",
    "titular_codigo_cargo_sobreposto",
    "titular_local_exercicio",
    "titular_local_servico",
)
_DETALHE_PERIODO = ("data_inicio", "data_fim")
_DETALHE_FLAGS = (
    "carater_excepcional",
    "com_afastamento",
    "possui_pendencia",
    "pendencias",
    "motivo_afastamento",
    "informacoes_adicionais",
    "detalhe_para_quadro_de_historico_por_ano",
)
_CAMPOS_DETALHE = (
    *_DETALHE_UNIDADE,
    *_DETALHE_INDICADO,
    *_DETALHE_TITULAR,
    *_DETALHE_PERIODO,
    *_DETALHE_FLAGS,
    "tipo_vaga",
    "cargo_vaga",
)
_CAMPOS_INTEIROS = frozenset(
    {
        "indicado_vinculo",
        "indicado_codigo_cargo_base",
        "indicado_codigo_cargo_sobreposto",
        "titular_vinculo",
        "titular_codigo_cargo_base",
        "titular_codigo_cargo_sobreposto",
        "cargo_vaga",
    }
)
_CAMPOS_BOOLEANOS = frozenset(
    {
        "indicado_possui_cargo_sobreposto",
        "carater_excepcional",
        "com_afastamento",
        "possui_pendencia",
        "detalhe_para_quadro_de_historico_por_ano",
    }
)
_CAMPOS_DATAS = frozenset({"data_inicio", "data_fim"})
_CAMPOS_NULOS = frozenset(
    {
        "indicado_codigo_cargo_base",
        "indicado_codigo_cargo_sobreposto",
        "titular_vinculo",
        "titular_codigo_cargo_base",
        "titular_codigo_cargo_sobreposto",
        "data_fim",
        "cargo_vaga",
    }
)
_CAMPOS_HISTORICO = (
    *_CAMPOS_ATO_INICIO,
    *_CAMPOS_PORTARIA,
    *_CAMPOS_ATO_FIM,
    *_CAMPOS_SERVIDOR,
    *_DETALHE_UNIDADE,
    *_DETALHE_INDICADO,
    *_DETALHE_TITULAR,
    *_DETALHE_PERIODO,
    *_DETALHE_FLAGS,
    "impedimento_substituicao",
    "impedimento_substituicao_detail",
    "impedimento_display",
    "tipo_vaga",
    "tipo_vaga_display",
    "cargo_vaga",
    "cargo_vaga_display",
    "vigente",
    "cessada_em",
    "atos_relacionados",
)


def _classe_do_campo_detalhe(nome: str) -> type[serializers.Field]:
    """Escolhe o tipo do campo de leitura conforme o nome no detalhe.

    Args:
        nome: Nome do campo em ``DesignacaoDetalhe``.

    Returns:
        type[serializers.Field]: Classe do campo DRF.

    """
    if nome in _CAMPOS_INTEIROS:
        return serializers.IntegerField
    if nome in _CAMPOS_BOOLEANOS:
        return serializers.BooleanField
    if nome in _CAMPOS_DATAS:
        return serializers.DateField
    return serializers.CharField


def _campo_do_detalhe(nome: str) -> serializers.Field:
    """Monta o campo somente leitura espelhado de ``DesignacaoDetalhe``.

    Args:
        nome: Nome do campo no detalhe e no payload.

    Returns:
        serializers.Field: Campo com ``source`` em ``designacao_detalhe``.

    """
    kwargs: dict[str, Any] = {
        "source": f"designacao_detalhe.{nome}",
        "read_only": True,
    }
    if nome in _CAMPOS_NULOS:
        kwargs["allow_null"] = True
    return _classe_do_campo_detalhe(nome)(**kwargs)


def _declarar_campos_do_detalhe(namespace: dict[str, Any]) -> None:
    """Inclui os campos simples do detalhe no serializer em construção.

    Args:
        namespace: Namespace da classe (o ``locals()`` do corpo dela).

    """
    for nome in _CAMPOS_DETALHE:
        namespace[nome] = _campo_do_detalhe(nome)


def _formatar_portaria(ato: AtoAdministrativo) -> str | None:
    """Retorna a portaria do ato no formato ``número/ano``.

    Args:
        ato: Instância de AtoAdministrativo.

    Returns:
        str|None: Portaria formatada ou None quando o ato não possui
        número de portaria (ex.: apostila criada sem herdar a portaria).

    """
    if ato.numero_portaria is None:
        return None
    return f"{ato.numero_portaria}/{ato.ano_vigente}".rstrip("/")


def _data_cessacao_valida(
    ato: AtoAdministrativo,
) -> datetime.date | None:
    """Retorna a data da cessação válida (ativa) de uma designação.

    Args:
        ato: Instância de AtoAdministrativo de designação.

    Returns:
        datetime.date|None: Data da cessação ou None quando a designação
        não possui cessação válida.

    """
    cessacao = next(
        (
            filho
            for filho in ato.filhos.all()
            if filho.tipo == AtoAdministrativo.Tipo.CESSACAO
            and filho.eh_valido
        ),
        None,
    )
    if cessacao is None:
        return None
    detalhe = getattr(cessacao, "cessacao_detalhe", None)
    return getattr(detalhe, "data_cessacao", None)


def _percorrer_descendentes(
    ato: AtoAdministrativo,
) -> list[tuple[AtoAdministrativo, int]]:
    """Percorre a árvore de atos derivados e devolve pares (ato, nível).

    A travessia usa ``ato.filhos.all()``, alimentado pelo cache de
    prefetch carregado em ``HistoricoDesignacaoService``, então não gera
    consultas ao banco. O resultado sai do mais recente para o mais antigo,
    independentemente do nível — netos e bisnetos aparecem intercalados
    entre os filhos conforme foram criados.

    Args:
        ato: Designação cujos descendentes serão percorridos.

    Returns:
        list[tuple[AtoAdministrativo, int]]: Atos derivados com o nível
        de cada um (1 = filho da designação).

    """
    pares: list[tuple[AtoAdministrativo, int]] = []
    pendentes: list[tuple[AtoAdministrativo, int]] = [
        (filho, 1) for filho in ato.filhos.all()
    ]

    while pendentes:
        atual, nivel = pendentes.pop(0)
        pares.append((atual, nivel))
        pendentes.extend((filho, nivel + 1) for filho in atual.filhos.all())

    pares.sort(key=lambda par: (par[0].criado_em, par[0].pk), reverse=True)
    return pares


def _ultimo_ato_vigente_id(
    derivados: list[tuple[AtoAdministrativo, int]],
) -> int | None:
    """Retorna o id do último ato ativo e vigente da lista.

    A lista chega do mais recente para o mais antigo, então basta
    devolver o primeiro ato que continua ativo
    (``eh_valido``) e vigente (``esta_vigente``). Todos os atos
    desfeitos (insubsistentes) são ignorados.

    Args:
        derivados: Atos derivados com o nível de cada um, em ordem
            decrescente de criação.

    Returns:
        int|None: Id do último ato ativo e vigente, ou None quando
        nenhum ato permanece em vigor.

    """
    return next(
        (
            ato.pk
            for ato, _nivel in derivados
            if ato.eh_valido and ato.esta_vigente
        ),
        None,
    )


class CessadaEmField(serializers.DateField):
    """Campo de data calculado a partir da cessação válida da designação."""

    def get_attribute(self, instance: Any) -> datetime.date | None:
        """Extrai a data de cessação válida da designação.

        Args:
            instance: Instância de AtoAdministrativo.

        Returns:
            datetime.date|None: Data da cessação ou None.

        """
        return _data_cessacao_valida(instance)


class AtoHistoricoBaseSerializer(
    AtoRelacionadoMixin, serializers.ModelSerializer
):
    """Campos de ato comuns à designação e aos seus atos relacionados.

    A nomenclatura é a mesma de ``AtoAdministrativoListSerializer``.
    """

    tipo_de_ato = serializers.SerializerMethodField()
    status = serializers.CharField(read_only=True)
    portaria = serializers.SerializerMethodField()
    nome = serializers.SerializerMethodField()
    cargo = serializers.SerializerMethodField()
    rf = serializers.SerializerMethodField()
    criado_por_nome = serializers.SerializerMethodField()

    class Meta:
        model = AtoAdministrativo
        fields = _CAMPOS_ATO

    # ── Helpers de detalhe ──────────────────────────────────────────────

    def _detalhe_da_designacao(self, obj: AtoAdministrativo) -> Any:
        """Retorna o ``DesignacaoDetalhe`` da designação de origem.

        Para a própria designação é o seu detalhe. Para um ato derivado,
        o detalhe vem do mapa ``designacao_por_raiz_id`` do contexto
        (montado com as linhas já carregadas), sem tocar em
        ``ato_raiz``/``ato_pai``.

        Args:
            obj: Instância de AtoAdministrativo.

        Returns:
            DesignacaoDetalhe|None: Detalhe da designação de origem.

        """
        if obj.tipo == AtoAdministrativo.Tipo.DESIGNACAO:
            return getattr(obj, "designacao_detalhe", None)

        detalhes: dict[int, Any] = (
            self.context.get("designacao_por_raiz_id") or {}
        )
        chave = obj.ato_raiz_id or obj.ato_pai_id
        if chave in detalhes:
            return detalhes[chave]
        # Dado legado sem `ato_raiz` preenchido: cai no caminho do mixin.
        return self._get_designacao_detalhe(obj)

    def _tipo_do_pai(self, obj: AtoAdministrativo) -> str | None:
        """Retorna o tipo do ato pai a partir do mapa do contexto.

        Args:
            obj: Instância de AtoAdministrativo.

        Returns:
            str|None: Tipo do pai ou None quando o ato não tem pai ou o
            pai não está no conjunto carregado.

        """
        if obj.ato_pai_id is None:
            return None
        tipos: dict[int, str] = self.context.get("tipo_por_id") or {}
        return tipos.get(obj.ato_pai_id)

    # ── Campos ──────────────────────────────────────────────────────────

    def get_tipo_de_ato(self, obj: AtoAdministrativo) -> str:
        """Retorna o tipo do ato em formato legível.

        Segue a mesma nomenclatura da listagem de atos administrativos:
        o tipo do filho é concatenado com o do pai, com os casos
        especiais de "Tornar sem efeito" e "Anulação de Apostila".

        Args:
            obj: Instância de AtoAdministrativo.

        Returns:
            str: Nome legível do tipo do ato.

        """
        tipo_pai = self._tipo_do_pai(obj)
        if tipo_pai is None or obj.tipo == AtoAdministrativo.Tipo.CESSACAO:
            return f"{obj.get_tipo_display()}"

        if obj.tipo == AtoAdministrativo.Tipo.INSUBSISTENCIA:
            if tipo_pai == AtoAdministrativo.Tipo.INSUBSISTENCIA:
                return "Tornar sem efeito"
            if tipo_pai == AtoAdministrativo.Tipo.APOSTILA:
                return "Anulação de Apostila"

        label_pai = AtoAdministrativo.Tipo(tipo_pai).label
        return f"{obj.get_tipo_display()} de {label_pai}"

    def get_portaria(self, obj: AtoAdministrativo) -> str | None:
        """Retorna a portaria do ato no formato ``número/ano``."""
        return _formatar_portaria(obj)

    def get_nome(self, obj: AtoAdministrativo) -> str | None:
        """Retorna o nome do servidor indicado na designação de origem.

        Equivale ao campo ``nome`` de ``PortariaListSerializer``.

        Args:
            obj: Instância de AtoAdministrativo.

        Returns:
            str|None: Nome do servidor indicado ou None se não houver.

        """
        detalhe = self._detalhe_da_designacao(obj)
        if detalhe is None:
            return None
        return (
            detalhe.indicado_nome_servidor
            or detalhe.indicado_nome_civil
            or None
        )

    def get_cargo(self, obj: AtoAdministrativo) -> str | None:
        """Retorna o cargo do servidor indicado.

        Prefere o cargo sobreposto e, na ausência dele, o cargo base —
        mesma regra de ``PortariaListSerializer.get_cargo``.

        Args:
            obj: Instância de AtoAdministrativo.

        Returns:
            str|None: Cargo do indicado.

        """
        detalhe = self._detalhe_da_designacao(obj)
        if detalhe is None:
            return None
        return (
            detalhe.indicado_cargo_sobreposto
            or detalhe.indicado_cargo_base
            or None
        )

    def get_rf(self, obj: AtoAdministrativo) -> str | None:
        """Retorna o RF do servidor indicado na designação de origem.

        Args:
            obj: Instância de AtoAdministrativo.

        Returns:
            str|None: RF do indicado ou None se não houver.

        """
        detalhe = self._detalhe_da_designacao(obj)
        if detalhe is None:
            return None
        return detalhe.indicado_rf or None

    def get_criado_por_nome(self, obj: AtoAdministrativo) -> str | None:
        """Retorna o nome do responsável pela criação do ato.

        Args:
            obj: Instância de AtoAdministrativo.

        Returns:
            str|None: Nome ou username do responsável, ou None se não
            houver.

        """
        responsavel = obj.criado_por
        if not responsavel:
            return None
        return responsavel.name or responsavel.username


class AtoRelacionadoHistoricoSerializer(AtoHistoricoBaseSerializer):
    """Serializa um ato derivado da designação (item da lista plana).

    Cada ato é uma linha independente; a hierarquia é dada por
    ``ato_pai_id`` e ``nivel``, sem aninhamento de listas. Os campos
    extras (``tipo_insubsistencia``, ``tipo_apostila``,
    ``data_designacao``, ``data_cessacao``) repetem os nomes usados na
    listagem de atos administrativos.
    """

    observacoes = serializers.SerializerMethodField()
    tipo_insubsistencia = serializers.SerializerMethodField()
    tipo_apostila = serializers.SerializerMethodField()
    data_designacao = serializers.SerializerMethodField()
    data_cessacao = serializers.SerializerMethodField()
    nivel = serializers.SerializerMethodField()
    ultimo_ato_vigente = serializers.SerializerMethodField()

    class Meta:
        model = AtoAdministrativo
        fields = _CAMPOS_ATO_RELACIONADO

    def get_observacoes(self, obj: AtoAdministrativo) -> str | None:
        """Retorna a observação do ato conforme o seu tipo.

        Mesma regra de ``PortariaListSerializer.get_observacoes``:
        insubsistência → ``observacoes``, apostila → ``observacao``,
        designação → ``informacoes_adicionais``; cessação não possui
        texto.

        Args:
            obj: Instância de AtoAdministrativo.

        Returns:
            str|None: Observação do ato ou None.

        """
        if obj.tipo == AtoAdministrativo.Tipo.INSUBSISTENCIA:
            detalhe = getattr(obj, "insubsistencia_detalhe", None)
            return getattr(detalhe, "observacoes", None)
        if obj.tipo == AtoAdministrativo.Tipo.APOSTILA:
            detalhe = getattr(obj, "apostila_detalhe", None)
            return getattr(detalhe, "observacao", None)
        if obj.tipo == AtoAdministrativo.Tipo.DESIGNACAO:
            detalhe = getattr(obj, "designacao_detalhe", None)
            return getattr(detalhe, "informacoes_adicionais", None)
        return None

    def get_tipo_insubsistencia(self, obj: AtoAdministrativo) -> str | None:
        """Retorna o tipo do ato pai quando este é uma insubsistência."""
        if obj.tipo != AtoAdministrativo.Tipo.INSUBSISTENCIA:
            return None
        return self._tipo_do_pai(obj)

    def get_tipo_apostila(self, obj: AtoAdministrativo) -> str | None:
        """Retorna o tipo do ato pai quando este é uma apostila."""
        if obj.tipo != AtoAdministrativo.Tipo.APOSTILA:
            return None
        return self._tipo_do_pai(obj)

    @extend_schema_field(OpenApiTypes.DATE)
    def get_data_designacao(self, obj: AtoAdministrativo) -> str | None:
        """Retorna a data de início da designação de origem (ISO)."""
        detalhe = self._detalhe_da_designacao(obj)
        data = getattr(detalhe, "data_inicio", None)
        return data.isoformat() if data else None

    @extend_schema_field(OpenApiTypes.DATE)
    def get_data_cessacao(self, obj: AtoAdministrativo) -> str | None:
        """Retorna a data de cessação quando o ato é uma cessação (ISO)."""
        if obj.tipo != AtoAdministrativo.Tipo.CESSACAO:
            return None
        detalhe = getattr(obj, "cessacao_detalhe", None)
        data = getattr(detalhe, "data_cessacao", None)
        return data.isoformat() if data else None

    def get_nivel(self, obj: AtoAdministrativo) -> int:
        """Retorna o nível do ato na hierarquia (1 = filho da designação).

        Args:
            obj: Instância de AtoAdministrativo.

        Returns:
            int: Profundidade do ato em relação à designação.

        """
        return int(self.context.get("nivel", 1))

    def get_ultimo_ato_vigente(self, obj: AtoAdministrativo) -> bool:
        """Indica se este é o último ato feito que ainda está em vigor.

        Na lista de atos de uma designação apenas um item recebe `True`:
        o mais recente que continua ativo (``eh_valido``) e vigente
        (``esta_vigente``). Se todos os atos já foram desfeitos, nenhum
        item é marcado.

        Args:
            obj: Instância de AtoAdministrativo.

        Returns:
            bool: True apenas para o último ato ativo e vigente.

        """
        return obj.pk == self.context.get("ultimo_ato_vigente_id")


class HistoricoDesignacaoSerializer(AtoHistoricoBaseSerializer):
    """Serializa uma designação da UE com detalhe completo e histórico.

    Os campos de detalhe repetem ``DesignacaoReadSerializer``; os campos
    de ato repetem ``AtoAdministrativoListSerializer``. Além deles, vêm
    ``vigente``, ``cessada_em`` e ``atos_relacionados``.
    """

    _declarar_campos_do_detalhe(locals())

    impedimento_substituicao: serializers.PrimaryKeyRelatedField = (
        serializers.PrimaryKeyRelatedField(
            source="designacao_detalhe.impedimento_substituicao",
            read_only=True,
        )
    )
    impedimento_substituicao_detail: ImpedimentoSubstituicaoSerializer = (
        ImpedimentoSubstituicaoSerializer(
            source="designacao_detalhe.impedimento_substituicao",
            read_only=True,
        )
    )
    impedimento_display = serializers.SerializerMethodField()
    tipo_vaga_display = serializers.SerializerMethodField()
    cargo_vaga_display = serializers.SerializerMethodField()

    # Situação e histórico
    vigente = serializers.BooleanField(source="esta_vigente", read_only=True)
    cessada_em = CessadaEmField(read_only=True, allow_null=True)
    atos_relacionados = serializers.SerializerMethodField()

    class Meta:
        model = AtoAdministrativo
        fields = _CAMPOS_HISTORICO

    def get_impedimento_display(self, obj: AtoAdministrativo) -> str | None:
        """Retorna a descrição do impedimento de substituição.

        Args:
            obj: Instância de AtoAdministrativo.

        Returns:
            str|None: Descrição do impedimento ou None se não houver.

        """
        detalhe = getattr(obj, "designacao_detalhe", None)
        impedimento = getattr(detalhe, "impedimento_substituicao", None)
        return impedimento.descricao if impedimento else None

    def get_tipo_vaga_display(self, obj: AtoAdministrativo) -> str | None:
        """Retorna o texto descritivo do tipo de vaga.

        Args:
            obj: Instância de AtoAdministrativo.

        Returns:
            str|None: Descrição do tipo de vaga ou None.

        """
        detalhe = getattr(obj, "designacao_detalhe", None)
        if detalhe is None:
            return None
        return detalhe.get_tipo_vaga_display()

    def get_cargo_vaga_display(self, obj: AtoAdministrativo) -> str | None:
        """Retorna a descrição completa do cargo de vaga da designação.

        O valor vem de ``cargo_base.descricao_completa``, ligado por
        ``codigo_cargo`` = ``designacao_detalhe.cargo_vaga`` na consulta
        do histórico (anotação ``descricao_cargo_vaga``).

        Args:
            obj: Instância de AtoAdministrativo de designação.

        Returns:
            str|None: Descrição completa do cargo ou None se não houver.

        """
        return getattr(obj, "descricao_cargo_vaga", None) or None

    @extend_schema_field(AtoRelacionadoHistoricoSerializer(many=True))
    def get_atos_relacionados(
        self, obj: AtoAdministrativo
    ) -> list[dict[str, Any]]:
        """Retorna todos os atos derivados da designação em uma lista plana.

        Percorre filhos, netos, bisnetos e demais níveis e devolve tudo
        em um único array, do mais recente para o mais antigo. A hierarquia é
        representada em cada item por ``ato_pai_id`` e ``nivel``.

        O item mais recente que ainda está ativo e vigente é marcado com
        ``ultimo_ato_vigente=True``; os demais ficam com ``False``.

        Args:
            obj: Instância de AtoAdministrativo.

        Returns:
            list[dict]: Todos os atos derivados da designação.

        """
        derivados = _percorrer_descendentes(obj)
        if not derivados:
            return []

        contexto = {
            **self.context,
            "ultimo_ato_vigente_id": _ultimo_ato_vigente_id(derivados),
            # Tipo de cada ato, para `tipo_de_ato`/`tipo_apostila`/
            # `tipo_insubsistencia` sem tocar em `ato_pai` (que seria uma
            # consulta por item). A designação de origem entra no mapa
            # para que os filhos diretos saiam como "X de Designação".
            "tipo_por_id": {
                obj.pk: obj.tipo,
                **{ato.pk: ato.tipo for ato, _nivel in derivados},
            },
            # Detalhe da designação de origem, para `nome`/`cargo`/`rf`
            # e `data_designacao`.
            "designacao_por_raiz_id": {obj.pk: self._detalhe_seguro(obj)},
        }

        return [
            cast(
                dict[str, Any],
                AtoRelacionadoHistoricoSerializer(
                    ato, context={**contexto, "nivel": nivel}
                ).data,
            )
            for ato, nivel in derivados
        ]

    @staticmethod
    def _detalhe_seguro(obj: AtoAdministrativo) -> Any:
        """Retorna o detalhe da designação sem levantar exceção.

        Args:
            obj: Instância de AtoAdministrativo de designação.

        Returns:
            DesignacaoDetalhe|None: Detalhe ou None se o ato não tiver
            detalhe associado.

        """
        return getattr(obj, "designacao_detalhe", None)
