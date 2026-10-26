"""Serviço de histórico de designações por unidade escolar.

Consulta as designações de uma UE e carrega, em **uma única consulta**,
todos os atos derivados delas (cessações, apostilas, insubsistências e os
filhos destes em qualquer profundidade). A hierarquia é montada em memória
para que a serialização não gere novas consultas ao banco.
"""

from collections import defaultdict

from django.db.models import Q, QuerySet

from apps.designacao.models.ato_administrativo import AtoAdministrativo
from apps.designacao.models.designacao_detalhe import DesignacaoDetalhe

# Código EOL de unidade escolar é numérico e normalmente gravado com zeros
# à esquerda (ex.: "019453"); o tamanho padrão é 6 dígitos.
_TAMANHO_CODIGO_UE = 6

# Relações OneToOne do ato com o seu detalhe. Todas viram LEFT JOIN na
# mesma linha do ato (custo de um lookup por pk), então vale carregá-las
# de uma vez em vez de deixar o serializer consultar cada uma.
_SELECT_RELATED_DETALHES = (
    "designacao_detalhe",
    "cessacao_detalhe",
    "apostila_detalhe",
    "insubsistencia_detalhe",
)

# Campos grandes que este endpoint não devolve: adiá-los evita trafegar
# textos longos (portaria inteira, pendências, informações adicionais) do
# banco para o processo Python em cada linha do histórico.
_CAMPOS_ADIADOS = (
    "texto_sei",
    "designacao_detalhe__pendencias",
    "designacao_detalhe__informacoes_adicionais",
    "designacao_detalhe__motivo_afastamento",
)


class HistoricoDesignacaoService:
    """Serviço de consulta do histórico de designações de uma UE."""

    @staticmethod
    def _variantes_codigo_ue(codigo_ue: str) -> set[str]:
        """Retorna as formas aceitas do código da UE.

        A mesma unidade pode estar gravada com zeros à esquerda
        (``019453``) ou sem eles (``19453``), dependendo da origem do
        cadastro. Para que a consulta funcione nas duas formas, são
        consideradas as variantes informada, sem zeros e com o
        preenchimento padrão do código EOL.

        Args:
            codigo_ue: Código informado na URL.

        Returns:
            set[str]: Variantes não vazias do código.

        """
        codigo = codigo_ue.strip()
        sem_zeros = codigo.lstrip("0")
        variantes = {codigo, sem_zeros}
        if sem_zeros.isdecimal():
            variantes.add(sem_zeros.zfill(_TAMANHO_CODIGO_UE))
        return variantes - {""}

    @classmethod
    def _ids_designacoes_da_ue(cls, codigo_ue: str) -> QuerySet:
        """Retorna um queryset com os ids das designações da UE.

        ``DesignacaoDetalhe.pk`` é o próprio id do ato (OneToOne com
        ``primary_key=True``), então ``values("pk")`` já entrega os ids
        de ``AtoAdministrativo``. Usado como subquery, evita materializar
        a lista de ids em Python e uma viagem extra ao banco.

        Args:
            codigo_ue: Código EOL da unidade escolar.

        Returns:
            QuerySet: Ids das designações da UE (subquery).

        """
        return DesignacaoDetalhe.objects.filter(
            ue__in=cls._variantes_codigo_ue(codigo_ue)
        ).values("pk")

    @classmethod
    def listar_por_ue(cls, codigo_ue: str) -> list[AtoAdministrativo]:
        """Retorna as designações da UE com os atos derivados carregados.

        As designações são devolvidas da mais recente para a mais antiga
        (data de início decrescente). Os filhos ficam disponíveis em
        ``ato.filhos.all()`` a partir do cache, sem consultas extras.

        Args:
            codigo_ue: Código EOL da unidade escolar.

        Returns:
            list[AtoAdministrativo]: Designações da UE com os atos
            derivados prontos para serialização.

        """
        ids_ue = cls._ids_designacoes_da_ue(codigo_ue)

        atos = list(
            AtoAdministrativo.objects.filter(
                # As próprias designações da UE...
                Q(pk__in=ids_ue)
                # ...e todos os descendentes delas, em qualquer nível.
                # `ato_raiz` sempre aponta para a designação de origem.
                | Q(ato_raiz_id__in=ids_ue)
            )
            .select_related(*_SELECT_RELATED_DETALHES)
            .defer(*_CAMPOS_ADIADOS)
        )

        if not atos:
            return []

        cls._preencher_filhos(atos)

        designacoes = [
            ato
            for ato in atos
            if ato.tipo == AtoAdministrativo.Tipo.DESIGNACAO
        ]
        designacoes.sort(
            key=lambda ato: (
                ato.designacao_detalhe.data_inicio,
                ato.criado_em,
            ),
            reverse=True,
        )
        return designacoes

    @staticmethod
    def _preencher_filhos(atos: list[AtoAdministrativo]) -> None:
        """Agrupa os atos por pai e alimenta o cache de ``filhos``.

        ``AtoAdministrativo.esta_vigente`` e ``AtoAdministrativo.status``
        consultam ``ato.filhos``. Preencher ``_prefetched_objects_cache``
        com a lista já carregada mantém a regra de negócio no model e
        evita uma consulta por ato.

        Args:
            atos: Atos da hierarquia (designações e descendentes).

        """
        filhos_por_pai: dict[int, list[AtoAdministrativo]] = defaultdict(list)
        for ato in atos:
            if ato.ato_pai_id is not None:
                filhos_por_pai[ato.ato_pai_id].append(ato)

        for ato in atos:
            # O prefetch do Django guarda uma lista nesse cache; o
            # RelatedManager devolve exatamente o que estiver ali.
            ato._prefetched_objects_cache = {  # type: ignore[attr-defined]
                "filhos": filhos_por_pai.get(ato.pk, [])
            }
