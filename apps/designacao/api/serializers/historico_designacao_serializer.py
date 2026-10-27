"""Serializadores do histórico de designações por unidade escolar.

Expõe a designação com seus dados principais, a situação de vigência e a
cessação válida, além de uma lista plana com todos os atos relacionados
(cessações, apostilas, insubsistências e seus descendentes em qualquer
nível), em ordem cronológica.
"""

import datetime
from typing import Any, cast

from drf_spectacular.utils import extend_schema_field
from rest_framework import serializers

from apps.designacao.api.serializers.ato_relacionado_mixin import (
    AtoRelacionadoMixin,
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


class AtoRelacionadoHistoricoSerializer(
    AtoRelacionadoMixin, serializers.ModelSerializer
):
    """Serializa um ato derivado da designação (item da lista plana).

    Cada ato é uma linha independente; a hierarquia é dada por
    ``ato_pai_id`` e ``nivel``, sem aninhamento de listas.
    """

    tipo_de_ato = serializers.SerializerMethodField()
    nivel = serializers.SerializerMethodField()
    data_do_ato = serializers.DateField(source="doc", allow_null=True)
    portaria = serializers.SerializerMethodField()
    nome_display = serializers.SerializerMethodField()
    observacao = serializers.SerializerMethodField()
    ultimo_ato_vigente = serializers.SerializerMethodField()

    class Meta:
        model = AtoAdministrativo
        fields = [
            "id",
            "ato_pai_id",
            "tipo",
            "tipo_de_ato",
            "nivel",
            "data_do_ato",
            "numero_portaria",
            "ano_vigente",
            "portaria",
            "nome_display",
            "observacao",
            "ativo",
            "ultimo_ato_vigente",
        ]

    def get_tipo_de_ato(self, obj: AtoAdministrativo) -> str:
        """Retorna o tipo do ato em formato legível.

        Segue a mesma nomenclatura da listagem de atos administrativos:
        o tipo do filho é concatenado com o do pai, com os casos
        especiais de "Tornar sem efeito" e "Anulação de Apostila".

        O tipo do pai vem do mapa ``tipo_por_id`` do contexto (montado a
        partir das linhas já carregadas), evitando o acesso a
        ``obj.ato_pai`` e a consulta que ele dispararia.

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

    def get_nivel(self, obj: AtoAdministrativo) -> int:
        """Retorna o nível do ato na hierarquia (1 = filho da designação).

        Args:
            obj: Instância de AtoAdministrativo.

        Returns:
            int: Profundidade do ato em relação à designação.

        """
        return int(self.context.get("nivel", 1))

    def get_portaria(self, obj: AtoAdministrativo) -> str | None:
        """Retorna a portaria do ato no formato ``número/ano``."""
        return _formatar_portaria(obj)

    def get_nome_display(self, obj: AtoAdministrativo) -> str | None:
        """Retorna o nome do servidor indicado na designação de origem.

        O nome vem do detalhe da designação raiz, já que os atos
        derivados não possuem servidor próprio. O detalhe é resolvido
        pelo mapa ``designacao_por_raiz_id`` do contexto, montado com o
        que já foi carregado — sem tocar em ``ato_raiz``/``ato_pai``.

        Args:
            obj: Instância de AtoAdministrativo.

        Returns:
            str|None: Nome do servidor indicado ou None se não houver.

        """
        detalhe = self._designacao_detalhe(obj)
        if detalhe is None:
            return None
        return (
            detalhe.indicado_nome_servidor
            or detalhe.indicado_nome_civil
            or None
        )

    def _designacao_detalhe(self, obj: AtoAdministrativo) -> Any:
        """Retorna o detalhe da designação de origem do ato.

        Args:
            obj: Instância de AtoAdministrativo.

        Returns:
            DesignacaoDetalhe|None: Detalhe da designação de origem.

        """
        detalhes: dict[int, Any] = (
            self.context.get("designacao_por_raiz_id") or {}
        )
        chave = obj.ato_raiz_id or obj.ato_pai_id
        if chave in detalhes:
            return detalhes[chave]
        # Dado legado sem `ato_raiz` preenchido: cai no caminho do mixin.
        return self._get_designacao_detalhe(obj)

    def get_observacao(self, obj: AtoAdministrativo) -> str | None:
        """Retorna a observação do ato conforme o seu tipo.

        Args:
            obj: Instância de AtoAdministrativo.

        Returns:
            str|None: Observação do ato ou None quando o tipo não possui
            texto de observação (ex.: cessação).

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


class HistoricoDesignacaoSerializer(
    AtoRelacionadoMixin, serializers.ModelSerializer
):
    """Serializa uma designação da UE com a sua situação e histórico."""

    status = serializers.CharField(read_only=True)
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
    indicado_rf = serializers.CharField(
        source="designacao_detalhe.indicado_rf", read_only=True
    )
    data_inicio = serializers.DateField(
        source="designacao_detalhe.data_inicio", read_only=True
    )
    data_fim = serializers.DateField(
        source="designacao_detalhe.data_fim", read_only=True, allow_null=True
    )
    portaria = serializers.SerializerMethodField()
    cargo = serializers.SerializerMethodField()
    servidor_indicado = serializers.SerializerMethodField()
    vigente = serializers.BooleanField(source="esta_vigente", read_only=True)
    cessada_em = CessadaEmField(read_only=True, allow_null=True)
    atos_relacionados = serializers.SerializerMethodField()

    class Meta:
        model = AtoAdministrativo
        fields = [
            "id",
            "status",
            "numero_portaria",
            "ano_vigente",
            "portaria",
            "sei_numero",
            "doc",
            "ue",
            "dre",
            "dre_nome",
            "unidade_proponente",
            "codigo_hierarquico",
            "cargo",
            "servidor_indicado",
            "indicado_rf",
            "data_inicio",
            "data_fim",
            "vigente",
            "cessada_em",
            "atos_relacionados",
        ]

    def get_portaria(self, obj: AtoAdministrativo) -> str | None:
        """Retorna a portaria da designação no formato ``número/ano``."""
        return _formatar_portaria(obj)

    def get_cargo(self, obj: AtoAdministrativo) -> str | None:
        """Retorna o cargo do servidor indicado.

        Prefere o cargo sobreposto e, na ausência dele, o cargo base.

        Args:
            obj: Instância de AtoAdministrativo.

        Returns:
            str|None: Cargo do indicado.

        """
        detalhe = getattr(obj, "designacao_detalhe", None)
        if detalhe is None:
            return None
        return (
            detalhe.indicado_cargo_sobreposto
            or detalhe.indicado_cargo_base
            or None
        )

    def get_servidor_indicado(self, obj: AtoAdministrativo) -> str | None:
        """Retorna o nome do servidor indicado na designação."""
        detalhe = getattr(obj, "designacao_detalhe", None)
        if detalhe is None:
            return None
        return (
            detalhe.indicado_nome_servidor
            or detalhe.indicado_nome_civil
            or None
        )

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
            # Tipo de cada ato, para `tipo_de_ato` concatenar com o pai
            # sem tocar em `ato_pai` (que seria uma consulta por item).
            # A designação de origem entra no mapa para que os filhos
            # diretos também saiam como "X de Designação".
            "tipo_por_id": {
                obj.pk: obj.tipo,
                **{ato.pk: ato.tipo for ato, _nivel in derivados},
            },
            # Detalhe da designação de origem, para o `nome_display`.
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
