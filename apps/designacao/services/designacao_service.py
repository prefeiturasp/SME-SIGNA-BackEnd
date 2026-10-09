"""Serviço de designação.

Gerencia a criação, atualização e consulta de cargos pareados para atos de
designação.
"""

import datetime

from django.db import transaction
from django.db.models import F, QuerySet
from rest_framework.exceptions import ValidationError

from apps.designacao.models.ato_administrativo import AtoAdministrativo
from apps.designacao.models.designacao_detalhe import DesignacaoDetalhe

_CAMPOS_ATO = frozenset(
    {
        "numero_portaria",
        "ano_vigente",
        "sei_numero",
        "doc",
        "criado_por",
        "texto_sei",
        "modelo_portaria",
    }
)

# Campos do detalhe que identificam a substituição (unidade, cargo,
# titular e tipo de vaga) e o seu período — usados na validação de
# sobreposição.
_CAMPOS_SOBREPOSICAO = frozenset(
    {
        "ue",
        "cargo_vaga",
        "titular_rf",
        "tipo_vaga",
        "data_inicio",
        "data_fim",
    }
)

CODIGO_PERIODO_SOBREPOSTO = "periodo_sobreposto"

# Campos que representam o texto congelado da portaria — uma vez que o
# ato é publicado no Diário Oficial (doc preenchido), esse texto passa a
# ser um registro histórico e não pode mais ser reescrito.
_CAMPOS_TEXTO_PORTARIA = frozenset({"texto_sei", "modelo_portaria"})


class DesignacaoService:
    """Serviço de negócio para atos de designação."""

    @classmethod
    def criar(cls, data: dict) -> AtoAdministrativo:
        """Cria um ato administrativo de designação.

        Args:
            data: Dicionário com os dados do ato e do detalhe de designação.

        Returns:
            AtoAdministrativo: Ato administrativo de designação criado.

        """
        data_ato = {k: v for k, v in data.items() if k in _CAMPOS_ATO}
        data_detalhe = {k: v for k, v in data.items() if k not in _CAMPOS_ATO}

        cls._validar_sobreposicao(data_detalhe)

        with transaction.atomic():
            ato = AtoAdministrativo.objects.create(
                tipo=AtoAdministrativo.Tipo.DESIGNACAO,
                status_publicacao=AtoAdministrativo.StatusPublicacao.NAO_PUBLICADO,
                **data_ato,
            )
            DesignacaoDetalhe.objects.create(ato=ato, **data_detalhe)

        return ato

    @classmethod
    def atualizar(
        cls, ato: AtoAdministrativo, data: dict
    ) -> AtoAdministrativo:
        """Atualiza um ato administrativo de designação e seu detalhe.

        Args:
            ato: Ato administrativo de designação existente.
            data: Dicionário com os campos a atualizar.

        Returns:
            AtoAdministrativo: Ato administrativo atualizado.

        """
        data_ato = {k: v for k, v in data.items() if k in _CAMPOS_ATO}
        data_detalhe = {k: v for k, v in data.items() if k not in _CAMPOS_ATO}

        if _CAMPOS_TEXTO_PORTARIA & data_ato.keys() and ato.esta_publicado:
            raise ValidationError(
                {
                    "texto_sei": (
                        "Não é possível alterar o texto da portaria de um "
                        "ato já publicado no Diário Oficial."
                    )
                }
            )

        if _CAMPOS_SOBREPOSICAO & data_detalhe.keys():
            detalhe_atual = ato.designacao_detalhe
            dados_efetivos = {
                campo: getattr(detalhe_atual, campo)
                for campo in _CAMPOS_SOBREPOSICAO
            }
            dados_efetivos.update(data_detalhe)
            cls._validar_sobreposicao(dados_efetivos, ignorar_ato=ato)

        with transaction.atomic():
            if data_ato:
                for field, value in data_ato.items():
                    setattr(ato, field, value)
                ato.save(update_fields=list(data_ato.keys()))

            if data_detalhe:
                detalhe = ato.designacao_detalhe
                for field, value in data_detalhe.items():
                    setattr(detalhe, field, value)
                detalhe.save(update_fields=list(data_detalhe.keys()))

        return ato

    @staticmethod
    def _fim_efetivo(ato: AtoAdministrativo) -> datetime.date | None:
        """Retorna o último dia de vigência de uma designação.

        Com cessação ativa, a designação termina na data da cessação; caso
        contrário, na data final. `None` indica vigência sem data final.

        Args:
            ato: Ato de designação (com `filhos` pré-carregados).

        Returns:
            datetime.date | None: Último dia de vigência.

        """
        cessacao = next(
            (
                f
                for f in ato.filhos.all()
                if f.tipo == AtoAdministrativo.Tipo.CESSACAO and f.ativo
            ),
            None,
        )
        if cessacao is not None:
            return cessacao.cessacao_detalhe.data_cessacao
        return ato.designacao_detalhe.data_fim

    @classmethod
    def _validar_sobreposicao(
        cls,
        dados: dict,
        ignorar_ato: AtoAdministrativo | None = None,
    ) -> None:
        """Bloqueia substituição cujo período choca com outra do titular.

        Aplica-se só às substituições — cargo disponível (`DISPONIVEL`) com
        titular informado; cargo vago ainda não é validado. Considera as
        substituições ativas do mesmo titular (`titular_rf`), no mesmo
        cargo (`cargo_vaga`) e unidade (`ue`), cujo período se sobrepõe ao
        informado. Os dois extremos são inclusivos: iniciar no mesmo dia em
        que a outra termina também é sobreposição. Sem data final, a
        designação é considerada vigente em aberto.

        Args:
            dados: Campos do detalhe de designação (valores efetivos).
            ignorar_ato: Designação a desconsiderar (a própria, na edição).

        Raises:
            ValidationError: Se houver sobreposição de período.

        """
        ue = dados.get("ue")
        cargo_vaga = dados.get("cargo_vaga")
        titular_rf = dados.get("titular_rf")
        data_inicio = dados.get("data_inicio")
        data_fim = dados.get("data_fim")
        if (
            dados.get("tipo_vaga") != DesignacaoDetalhe.TipoVaga.DISPONIVEL
            or not ue
            or cargo_vaga is None
            or not titular_rf
            or data_inicio is None
        ):
            return

        atos = (
            AtoAdministrativo.objects.filter(
                tipo=AtoAdministrativo.Tipo.DESIGNACAO,
                ativo=True,
                designacao_detalhe__tipo_vaga=DesignacaoDetalhe.TipoVaga.DISPONIVEL,
                designacao_detalhe__ue=ue,
                designacao_detalhe__cargo_vaga=cargo_vaga,
                designacao_detalhe__titular_rf=titular_rf,
            )
            .select_related("designacao_detalhe")
            .prefetch_related("filhos__cessacao_detalhe")
        )
        if data_fim is not None:
            atos = atos.filter(designacao_detalhe__data_inicio__lte=data_fim)
        if ignorar_ato is not None:
            atos = atos.exclude(pk=ignorar_ato.pk)

        fins_sobrepostos = []
        for ato in atos:
            fim = cls._fim_efetivo(ato)
            if fim is None or fim >= data_inicio:
                fins_sobrepostos.append(fim)

        if not fins_sobrepostos:
            return

        raise ValidationError(
            {"data_inicio": [cls._mensagem_sobreposicao(fins_sobrepostos)]},
            code=CODIGO_PERIODO_SOBREPOSTO,
        )

    @staticmethod
    def _mensagem_sobreposicao(fins: list[datetime.date | None]) -> str:
        """Monta a mensagem de bloqueio por sobreposição de período.

        Args:
            fins: Últimos dias de vigência das designações sobrepostas.

        Returns:
            str: Mensagem explicando o conflito e a data mínima de início.

        """
        if None in fins:
            return (
                "Já existe designação vigente em substituição a este "
                "titular, para este cargo nesta unidade, sem data final. "
                "Encerre-a antes de registrar uma nova designação."
            )
        ultimo_dia = max(f for f in fins if f is not None)
        dia_seguinte = ultimo_dia + datetime.timedelta(days=1)
        return (
            "Já existe designação em substituição a este titular, para "
            "este cargo nesta unidade, vigente até "
            f"{ultimo_dia:%d/%m/%Y}. A nova designação só pode iniciar "
            f"a partir do dia seguinte ao término da anterior "
            f"({dia_seguinte:%d/%m/%Y})."
        )

    @staticmethod
    def excluir(ato: AtoAdministrativo) -> None:
        """Remove um ato administrativo de designação.

        Impede a exclusão quando existirem atos derivados (cessação,
        apostila ou insubsistência) associados a esta designação, já que
        essas referências são protegidas contra exclusão em cascata.

        Args:
            ato: Ato administrativo de designação a ser removido.

        Raises:
            ValidationError: Se existirem atos derivados associados a
            esta designação.

        """
        tipos_dependentes = (
            ato.descendentes.order_by("tipo")
            .values_list("tipo", flat=True)
            .distinct()
        )
        if tipos_dependentes:
            labels = ", ".join(
                AtoAdministrativo.Tipo(tipo).label
                for tipo in tipos_dependentes
            )
            raise ValidationError(
                {
                    "detail": "Não é possível excluir esta designação: "
                    f"existem atos derivados ({labels}) associados a ela. "
                    "Exclua-os primeiro."
                }
            )
        ato.delete()

    @staticmethod
    def get_cargos_pareados(
        queryset: QuerySet,
        cod1: str,
        nome1: str,
        cod2: str,
        nome2: str,
    ) -> list:
        """Retorna cargos pareados a partir de um queryset.

        Args:
            queryset: QuerySet com os dados de cargos.
            cod1: Nome do campo de código do primeiro cargo.
            nome1: Nome do campo de nome do primeiro cargo.
            cod2: Nome do campo de código do segundo cargo.
            nome2: Nome do campo de nome do segundo cargo.

        Returns:
            list: Lista de cargos pareados ordenados por nome.

        """
        qs1 = (
            queryset.values(codigo=F(cod1), nome=F(nome1))
            .filter(**{f"{cod1}__isnull": False})
            .exclude(**{nome1: ""})
        )
        qs2 = (
            queryset.values(codigo=F(cod2), nome=F(nome2))
            .filter(**{f"{cod2}__isnull": False})
            .exclude(**{nome2: ""})
        )

        resultado = [
            {"codigoCargo": item["codigo"], "nomeCargo": item["nome"]}
            for item in qs1.union(qs2)
            if item["nome"]
        ]
        resultado.sort(key=lambda x: x["nomeCargo"])
        return resultado
