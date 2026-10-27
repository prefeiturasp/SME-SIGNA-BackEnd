"""Serviço de histórico de designações por unidade escolar.

Consulta as designações de uma UE e carrega, em **uma única consulta**,
todos os atos derivados delas (cessações, apostilas, insubsistências e os
filhos destes em qualquer profundidade). A hierarquia é montada em memória
para que a serialização não gere novas consultas ao banco.
"""

from collections import defaultdict
from typing import Any

from django.db.models import Q, QuerySet
from django.http import QueryDict
from rest_framework.exceptions import ValidationError

from apps.designacao.api.filters.historico_designacao_filter import (
    HistoricoDesignacaoFilter,
)
from apps.designacao.models.ato_administrativo import AtoAdministrativo
from apps.gestao.models.cargo_base import CargoBase

# Código EOL de unidade escolar é numérico e normalmente gravado com zeros
# à esquerda (ex.: "019453"); o tamanho padrão é 6 dígitos.
_TAMANHO_CODIGO_UE = 6

# Relações OneToOne do ato com o seu detalhe. Todas viram LEFT JOIN na
# mesma linha do ato (custo de um lookup por pk), então vale carregá-las
# de uma vez em vez de deixar o serializer consultar cada uma. O
# impedimento e o usuário criador também entram: o payload do histórico
# expõe `impedimento_*` e `criado_por_nome`, como a listagem de atos.
_SELECT_RELATED_DETALHES = (
    "designacao_detalhe",
    "designacao_detalhe__impedimento_substituicao",
    "cessacao_detalhe",
    "apostila_detalhe",
    "insubsistencia_detalhe",
    "criado_por",
)

# Único campo grande que este endpoint não devolve: o texto integral da
# portaria (`texto_sei`). Adiá-lo evita trafegar megabytes do banco para o
# processo Python em cada linha do histórico — quem precisa do texto usa
# `atos-administrativos/<id>/`.
_CAMPOS_ADIADOS = ("texto_sei",)


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
    def _designacoes_da_ue(
        cls,
        codigo_ue: str,
        filtros: QueryDict | dict[str, Any] | None = None,
    ) -> QuerySet:
        """Retorna o queryset de designações da UE, já filtrado.

        O queryset é usado como subquery da consulta principal: com isso
        os filtros não precisam de nenhuma consulta extra, e o filtro por
        `ue` continua aproveitando o índice de `designacao_detalhe.ue`.

        Args:
            codigo_ue: Código EOL da unidade escolar.
            filtros: Parâmetros de query string (``status_publicacao``,
                ``periodo_after``, ``periodo_before``, ``observacao``).

        Returns:
            QuerySet: Designações da UE que satisfazem os filtros.

        Raises:
            ValidationError: Quando algum filtro recebe valor inválido.

        """
        designacoes = AtoAdministrativo.objects.filter(
            tipo=AtoAdministrativo.Tipo.DESIGNACAO,
            designacao_detalhe__ue__in=cls._variantes_codigo_ue(codigo_ue),
        )
        if not filtros:
            return designacoes

        filtro = HistoricoDesignacaoFilter(data=filtros, queryset=designacoes)
        if not filtro.is_valid():
            raise ValidationError(filtro.errors)
        return filtro.qs

    @classmethod
    def listar_por_ue(
        cls,
        codigo_ue: str,
        filtros: QueryDict | dict[str, Any] | None = None,
    ) -> list[AtoAdministrativo]:
        """Retorna as designações da UE com os atos derivados carregados.

        As designações são devolvidas da mais recente para a mais antiga
        (data de início decrescente). Os filhos ficam disponíveis em
        ``ato.filhos.all()`` a partir do cache, sem consultas extras.

        Args:
            codigo_ue: Código EOL da unidade escolar.
            filtros: Parâmetros de query string que restringem quais
                designações entram na resposta. Os atos relacionados das
                designações filtradas são devolvidos por inteiro.

        Returns:
            list[AtoAdministrativo]: Designações da UE com os atos
            derivados prontos para serialização.

        Raises:
            ValidationError: Quando algum filtro recebe valor inválido.

        """
        ids_ue = cls._designacoes_da_ue(codigo_ue, filtros).values("pk")

        atos = list(
            AtoAdministrativo.objects.filter(
                # As próprias designações que passaram nos filtros...
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
        cls._preencher_descricoes_de_cargo(designacoes)
        return designacoes

    @staticmethod
    def _preencher_descricoes_de_cargo(
        designacoes: list[AtoAdministrativo],
    ) -> None:
        """Anexa a descrição do cargo de vaga a cada designação.

        O serializer expõe ``cargo_vaga_display`` (igual a
        ``DesignacaoReadSerializer``). Para não fazer uma consulta por
        designação, as descrições são buscadas **uma única vez** e
        guardadas em ``_cargo_por_codigo`` na instância. Quando nenhuma
        designação tem ``cargo_vaga``, nenhuma consulta extra é feita.

        Args:
            designacoes: Designações já ordenadas.

        """
        if not designacoes:
            return

        codigos = {
            str(detalhe.cargo_vaga)
            for detalhe in (
                ato.designacao_detalhe
                for ato in designacoes
                if ato.designacao_detalhe is not None
            )
            if detalhe.cargo_vaga is not None
        }
        mapa: dict[str, str] = {}
        if codigos:
            mapa = dict(
                CargoBase.objects.filter(codigo_cargo__in=codigos).values_list(
                    "codigo_cargo", "descricao_completa"
                )
            )
        for ato in designacoes:
            ato._cargo_por_codigo = mapa  # type: ignore[attr-defined]

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
