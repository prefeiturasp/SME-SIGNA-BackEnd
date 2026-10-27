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
    consultas ao banco. O resultado sai em ordem cronológica de criação,
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

    pares.sort(key=lambda par: (par[0].criado_em, par[0].pk))
    return pares


def _ultimo_ato_vigente_id(
    derivados: list[tuple[AtoAdministrativo, int]],
) -> int | None:
    """Retorna o id do último ato ativo e vigente da lista.

    A lista chega em ordem cronológica, então basta percorrê-la de trás
    para frente e devolver o primeiro ato que continua ativo
    (``eh_valido``) e vigente (``esta_vigente``). Todos os atos
    desfeitos (insubsistentes) são ignorados.

    Args:
        derivados: Atos derivados com o nível de cada um, em ordem
            cronológica.

    Returns:
        int|None: Id do último ato ativo e vigente, ou None quando
        nenhum ato permanece em vigor.

    """
    return next(
        (
            ato.pk
            for ato, _nivel in reversed(derivados)
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
        fields = [
            "id",
            "tipo",
            "tipo_de_ato",
            "status",
            "status_publicacao",
            "numero_portaria",
            "ano_vigente",
            "sei_numero",
            "doc",
            "portaria",
            "nome",
            "cargo",
            "rf",
            "ato_pai_id",
            "ato_raiz_id",
            "criado_em",
            "criado_por_nome",
        ]

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
        fields = [
            "id",
            "tipo",
            "tipo_de_ato",
            "status",
            "status_publicacao",
            "ativo",
            "numero_portaria",
            "ano_vigente",
            "sei_numero",
            "doc",
            "portaria",
            "data_designacao",
            "data_cessacao",
            "nome",
            "cargo",
            "rf",
            "observacoes",
            "tipo_insubsistencia",
            "tipo_apostila",
            "ato_pai_id",
            "ato_raiz_id",
            "criado_em",
            "criado_por_nome",
            "nivel",
            "ultimo_ato_vigente",
        ]

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

    # Unidade (DesignacaoDetalhe)
    ue = serializers.CharField(source="designacao_detalhe.ue", read_only=True)
    dre = serializers.CharField(
        source="designacao_detalhe.dre", read_only=True
    )
    dre_nome = serializers.CharField(
        source="designacao_detalhe.dre_nome", read_only=True
    )
    unidade_proponente = serializers.CharField(
        source="designacao_detalhe.unidade_proponente", read_only=True
    )
    codigo_hierarquico = serializers.CharField(
        source="designacao_detalhe.codigo_hierarquico", read_only=True
    )
    funcionarios_da_unidade = serializers.CharField(
        source="designacao_detalhe.funcionarios_da_unidade", read_only=True
    )

    # Indicado (DesignacaoDetalhe)
    indicado_nome_civil = serializers.CharField(
        source="designacao_detalhe.indicado_nome_civil", read_only=True
    )
    indicado_nome_servidor = serializers.CharField(
        source="designacao_detalhe.indicado_nome_servidor", read_only=True
    )
    indicado_rf = serializers.CharField(
        source="designacao_detalhe.indicado_rf", read_only=True
    )
    indicado_vinculo = serializers.IntegerField(
        source="designacao_detalhe.indicado_vinculo", read_only=True
    )
    indicado_cargo_base = serializers.CharField(
        source="designacao_detalhe.indicado_cargo_base", read_only=True
    )
    indicado_codigo_cargo_base = serializers.IntegerField(
        source="designacao_detalhe.indicado_codigo_cargo_base",
        read_only=True,
        allow_null=True,
    )
    indicado_lotacao = serializers.CharField(
        source="designacao_detalhe.indicado_lotacao", read_only=True
    )
    indicado_cargo_sobreposto = serializers.CharField(
        source="designacao_detalhe.indicado_cargo_sobreposto", read_only=True
    )
    indicado_codigo_cargo_sobreposto = serializers.IntegerField(
        source="designacao_detalhe.indicado_codigo_cargo_sobreposto",
        read_only=True,
        allow_null=True,
    )
    indicado_local_exercicio = serializers.CharField(
        source="designacao_detalhe.indicado_local_exercicio", read_only=True
    )
    indicado_local_servico = serializers.CharField(
        source="designacao_detalhe.indicado_local_servico", read_only=True
    )
    indicado_categoria = serializers.CharField(
        source="designacao_detalhe.indicado_categoria", read_only=True
    )
    indicado_codigo_ue_lotacao = serializers.CharField(
        source="designacao_detalhe.indicado_codigo_ue_lotacao",
        read_only=True,
    )
    indicado_possui_cargo_sobreposto = serializers.BooleanField(
        source="designacao_detalhe.indicado_possui_cargo_sobreposto",
        read_only=True,
    )

    # Titular (DesignacaoDetalhe)
    titular_nome_civil = serializers.CharField(
        source="designacao_detalhe.titular_nome_civil", read_only=True
    )
    titular_nome_servidor = serializers.CharField(
        source="designacao_detalhe.titular_nome_servidor", read_only=True
    )
    titular_rf = serializers.CharField(
        source="designacao_detalhe.titular_rf", read_only=True
    )
    titular_vinculo = serializers.IntegerField(
        source="designacao_detalhe.titular_vinculo",
        read_only=True,
        allow_null=True,
    )
    titular_cargo_base = serializers.CharField(
        source="designacao_detalhe.titular_cargo_base", read_only=True
    )
    titular_codigo_cargo_base = serializers.IntegerField(
        source="designacao_detalhe.titular_codigo_cargo_base",
        read_only=True,
        allow_null=True,
    )
    titular_lotacao = serializers.CharField(
        source="designacao_detalhe.titular_lotacao", read_only=True
    )
    titular_cargo_sobreposto = serializers.CharField(
        source="designacao_detalhe.titular_cargo_sobreposto", read_only=True
    )
    titular_codigo_cargo_sobreposto = serializers.IntegerField(
        source="designacao_detalhe.titular_codigo_cargo_sobreposto",
        read_only=True,
        allow_null=True,
    )
    titular_local_exercicio = serializers.CharField(
        source="designacao_detalhe.titular_local_exercicio", read_only=True
    )
    titular_local_servico = serializers.CharField(
        source="designacao_detalhe.titular_local_servico", read_only=True
    )

    # Período (DesignacaoDetalhe)
    data_inicio = serializers.DateField(
        source="designacao_detalhe.data_inicio", read_only=True
    )
    data_fim = serializers.DateField(
        source="designacao_detalhe.data_fim", read_only=True, allow_null=True
    )

    # Flags (DesignacaoDetalhe)
    carater_excepcional = serializers.BooleanField(
        source="designacao_detalhe.carater_excepcional", read_only=True
    )
    com_afastamento = serializers.BooleanField(
        source="designacao_detalhe.com_afastamento", read_only=True
    )
    possui_pendencia = serializers.BooleanField(
        source="designacao_detalhe.possui_pendencia", read_only=True
    )
    pendencias = serializers.CharField(
        source="designacao_detalhe.pendencias", read_only=True
    )
    motivo_afastamento = serializers.CharField(
        source="designacao_detalhe.motivo_afastamento", read_only=True
    )
    informacoes_adicionais = serializers.CharField(
        source="designacao_detalhe.informacoes_adicionais", read_only=True
    )
    detalhe_para_quadro_de_historico_por_ano = serializers.BooleanField(
        source="designacao_detalhe.detalhe_para_quadro_de_historico_por_ano",
        read_only=True,
    )

    # Impedimento (DesignacaoDetalhe)
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

    # Vaga (DesignacaoDetalhe)
    tipo_vaga = serializers.CharField(
        source="designacao_detalhe.tipo_vaga", read_only=True
    )
    tipo_vaga_display = serializers.SerializerMethodField()
    cargo_vaga = serializers.IntegerField(
        source="designacao_detalhe.cargo_vaga", read_only=True, allow_null=True
    )
    cargo_vaga_display = serializers.SerializerMethodField()

    # Situação e histórico
    vigente = serializers.BooleanField(source="esta_vigente", read_only=True)
    cessada_em = CessadaEmField(read_only=True, allow_null=True)
    atos_relacionados = serializers.SerializerMethodField()

    class Meta:
        model = AtoAdministrativo
        fields = [
            # Ato
            "id",
            "tipo",
            "tipo_de_ato",
            "status",
            "status_publicacao",
            "numero_portaria",
            "ano_vigente",
            "sei_numero",
            "doc",
            "portaria",
            "ato_pai_id",
            "ato_raiz_id",
            "criado_em",
            "criado_por_nome",
            # Servidor (derivados, como em atos administrativos)
            "nome",
            "cargo",
            "rf",
            # Unidade
            "ue",
            "dre",
            "dre_nome",
            "unidade_proponente",
            "codigo_hierarquico",
            "funcionarios_da_unidade",
            # Indicado
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
            # Titular
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
            # Período
            "data_inicio",
            "data_fim",
            # Flags
            "carater_excepcional",
            "com_afastamento",
            "possui_pendencia",
            "pendencias",
            "motivo_afastamento",
            "informacoes_adicionais",
            "detalhe_para_quadro_de_historico_por_ano",
            # Impedimento
            "impedimento_substituicao",
            "impedimento_substituicao_detail",
            "impedimento_display",
            # Vaga
            "tipo_vaga",
            "tipo_vaga_display",
            "cargo_vaga",
            "cargo_vaga_display",
            # Histórico
            "vigente",
            "cessada_em",
            "atos_relacionados",
        ]

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
        """Retorna a descrição completa do cargo de vaga.

        O mapa ``código → descrição`` é carregado uma única vez pelo
        serviço (``_cargo_por_codigo``) — sem uma consulta por
        designação.

        Args:
            obj: Instância de AtoAdministrativo.

        Returns:
            str|None: Descrição do cargo ou None se não houver.

        """
        detalhe = getattr(obj, "designacao_detalhe", None)
        codigo = getattr(detalhe, "cargo_vaga", None)
        if codigo is None:
            return None
        mapa: dict[str, str] = getattr(obj, "_cargo_por_codigo", None) or (
            self.context.get("cargo_por_codigo") or {}
        )
        return mapa.get(str(codigo))

    @extend_schema_field(AtoRelacionadoHistoricoSerializer(many=True))
    def get_atos_relacionados(
        self, obj: AtoAdministrativo
    ) -> list[dict[str, Any]]:
        """Retorna todos os atos derivados da designação em uma lista plana.

        Percorre filhos, netos, bisnetos e demais níveis e devolve tudo
        em um único array, em ordem cronológica. A hierarquia é
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
