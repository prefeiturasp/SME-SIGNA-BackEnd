"""Serviço de apostila.

Contém regras para criação de apostilas nos modelos legado e v2,
incluindo validações e aplicação de alterações em atos administrativos.
"""

import datetime
from typing import Any

from django.db import transaction
from django.db.models import QuerySet
from rest_framework.exceptions import ValidationError

from apps.designacao.models.apostila import Apostila
from apps.designacao.models.apostila_detalhe import (
    ApostilaAlteracao,
    ApostilaDetalhe,
)
from apps.designacao.models.ato_administrativo import AtoAdministrativo
from apps.designacao.models.designacao import Designacao

_CAMPOS_ATO = frozenset({"sei_numero", "doc"})
_CAMPOS_PROTEGIDOS = frozenset(
    {
        "id",
        "tipo",
        "ato_pai",
        "ato_pai_id",
        "ato_raiz",
        "ato_raiz_id",
        "criado_em",
    }
)
_CAMPOS_EXCLUIDOS_DETALHE = frozenset({"ato_id", "ato"})


class ApostilaService:
    """Serviço de negócio para manipular apostilas."""

    # ── Querysets ────────────────────────────────────────────────────────────

    @staticmethod
    def listar() -> QuerySet:
        """Retorna queryset de apostilas ativas (modelo legado)."""
        return (
            Apostila.objects.filter(is_deleted=False)
            .select_related("designacao", "cessacao")
            .order_by("-criado_em")
        )

    @staticmethod
    def listar_v2() -> QuerySet:
        """Retorna queryset de apostilas v2 (AtoAdministrativo)."""
        return (
            AtoAdministrativo.objects.filter(
                tipo=AtoAdministrativo.Tipo.APOSTILA
            )
            .select_related(
                "apostila_detalhe",
                "ato_pai__designacao_detalhe",
                "ato_raiz__designacao_detalhe",
                "ato_pai__cessacao_detalhe",
            )
            .prefetch_related(
                "apostila_detalhe__alteracoes",
                "filhos",
                "filhos__insubsistencia_detalhe",
            )
            .order_by("-criado_em")
        )

    @staticmethod
    def buscar_v2(pk: int) -> AtoAdministrativo | None:
        """Retorna uma apostila v2 por pk com todos os prefetches."""
        return ApostilaService.listar_v2().filter(pk=pk).first()

    # ── Legado (modelo Apostila) ──────────────────────────────────────────────  # noqa: E501

    @staticmethod
    def criar_apostila(data: dict) -> Apostila:
        """Cria uma apostila no modelo legado.

        Args:
            data: Dicionário com os dados necessários para criar a apostila.

        Returns:
            Apostila: Instância de apostila criada.

        Raises:
            ValidationError: Se a designação ou cessação não for válida
            ou se já existir uma apostila ativa.

        """
        designacao_id = data.pop("designacao")
        ato_apostilado = data.pop("ato_apostilado")

        designacao = (
            Designacao.objects.filter(id=designacao_id, is_deleted=False)
            .select_related("cessacao")
            .first()
        )

        if not designacao:
            raise ValidationError("Designação não encontrada.")

        if ato_apostilado == "designacao":
            alvo_designacao = designacao
            alvo_cessacao = None

        elif ato_apostilado == "cessacao":
            cessacao = getattr(designacao, "cessacao", None)

            if not cessacao or cessacao.is_deleted:
                raise ValidationError(
                    "Não existe cessação válida para esta designação."
                )

            alvo_designacao = None
            alvo_cessacao = cessacao

        else:
            raise ValidationError("Tipo de ato inválido.")

        alvo = alvo_designacao or alvo_cessacao

        if alvo is None:
            raise ValidationError("Ato alvo não encontrado para apostila.")

        if getattr(alvo, "is_deleted", False):
            raise ValidationError("Não é possível apostilar um ato deletado.")

        queryset = Apostila.objects.filter(
            is_deleted=False, tipo=Apostila.Tipo.APOSTILA
        )

        if alvo_designacao:
            queryset = queryset.filter(designacao=alvo_designacao)
        else:
            queryset = queryset.filter(cessacao=alvo_cessacao)

        apostilas_ativas = queryset.exclude(
            id__in=Apostila.objects.filter(
                tipo=Apostila.Tipo.ANULACAO,
                apostila_referencia__in=queryset,
            ).values_list("apostila_referencia_id", flat=True)
        )

        if apostilas_ativas.exists():
            raise ValidationError(
                "Já existe uma apostila válida para este ato."
            )

        from typing import cast

        return Apostila.objects.create(
            tipo=cast(str, data.get("tipo")),
            designacao=alvo_designacao,
            cessacao=alvo_cessacao,
            sei_numero=cast(str, data.get("sei_numero")),
            observacao=cast(str, data.get("observacao")),
            d_o=cast(str, data.get("d_o", "")),
        )

    # ── V2 (modelo AtoAdministrativo) ────────────────────────────────────────

    @staticmethod
    def criar(data: dict) -> AtoAdministrativo:
        """Cria um ato administrativo do tipo apostila (v2).

        Args:
            data: Dicionário com os dados do ato e alterações associadas.

        Returns:
            AtoAdministrativo: Ato administrativo de apostila criado.

        Raises:
            ValidationError: Se o ato pai for inválido ou não puder ser
            apostilado.

        """
        ato_pai: AtoAdministrativo = data["ato_pai"]
        alteracoes: list = data.get("alteracoes", [])

        if not ato_pai.eh_valido:
            raise ValidationError({"ato_pai": "Este ato está insubsistente."})

        if ato_pai.tipo == AtoAdministrativo.Tipo.DESIGNACAO:
            tem_cessacao_ativa = ato_pai.filhos.filter(
                tipo=AtoAdministrativo.Tipo.CESSACAO, ativo=True
            ).exists()
            if tem_cessacao_ativa:
                raise ValidationError(
                    {
                        "ato_pai": "Não é possível apostilar uma designação cessada."  # noqa: E501
                    }
                )

            detalhe = getattr(ato_pai, "designacao_detalhe", None)
            if (
                detalhe
                and detalhe.data_fim
                and detalhe.data_fim < datetime.date.today()
            ):
                raise ValidationError(
                    {
                        "ato_pai": "Não é possível apostilar uma designação com prazo finalizado."  # noqa: E501
                    }
                )

        data_ato = {k: v for k, v in data.items() if k in _CAMPOS_ATO}

        with transaction.atomic():
            ato = AtoAdministrativo.objects.create(
                tipo=AtoAdministrativo.Tipo.APOSTILA,
                status_publicacao=AtoAdministrativo.StatusPublicacao.NAO_PUBLICADO,
                ato_pai=ato_pai,
                **data_ato,
            )
            apostila_detalhe = ApostilaDetalhe.objects.create(
                ato=ato,
                observacao=data["observacao"],
            )

            if alteracoes:
                ApostilaService._aplicar_alteracoes(
                    ato_pai, apostila_detalhe, alteracoes
                )

        return ato

    @staticmethod
    def _encontrar_campo(
        campo: str,
        ato_pai: AtoAdministrativo,
        detalhe: Any | None,
    ) -> tuple[str, str]:
        """Encontra o campo a ser alterado no ato pai ou no detalhe.

        Args:
            campo: Nome do campo a ser alterado.
            ato_pai: Ato administrativo pai sobre o qual a apostila é aplicada.
            detalhe: Detalhe associado ao ato pai, se existir.

        Returns:
            tuple[str, str]: Tupla com destino ('ato_pai' ou
            'detalhe') e valor anterior.

        Raises:
            ValidationError: Se o campo não existir no ato pai ou detalhe.

        """
        if hasattr(ato_pai, campo):
            raw = getattr(ato_pai, campo)
            return "ato_pai", ("" if raw is None else str(raw))
        if (
            detalhe
            and hasattr(detalhe, campo)
            and campo not in _CAMPOS_EXCLUIDOS_DETALHE
        ):
            raw = getattr(detalhe, campo)
            return "detalhe", ("" if raw is None else str(raw))
        raise ValidationError(
            {"alteracoes": f"Campo '{campo}' não encontrado no ato pai."}
        )

    @staticmethod
    def _aplicar_alteracoes(
        ato_pai: AtoAdministrativo,
        apostila_detalhe: ApostilaDetalhe,
        alteracoes: list,
    ) -> None:
        """Aplica as alterações de uma apostila ao ato pai e ao detalhe.

        Args:
            ato_pai: Ato administrativo original que está sendo apostilado.
            apostila_detalhe: Registro de detalhe da apostila.
            alteracoes: Lista de alterações a serem aplicadas.

        """
        detalhe = ApostilaService._get_detalhe(ato_pai)
        buckets: dict[str, dict] = {"ato_pai": {}, "detalhe": {}}
        registros = []

        for alt in alteracoes:
            campo = alt["campo_alterado"]
            valor_novo = str(alt["valor_novo"])

            if campo in _CAMPOS_PROTEGIDOS:
                raise ValidationError(
                    {
                        "alteracoes": f"Campo '{campo}' não pode ser alterado via apostila."  # noqa: E501
                    }
                )

            destino, valor_anterior = ApostilaService._encontrar_campo(
                campo, ato_pai, detalhe
            )
            buckets[destino][campo] = valor_novo

            registros.append(
                ApostilaAlteracao(
                    apostila=apostila_detalhe,
                    campo_alterado=campo,
                    valor_anterior=valor_anterior,
                    valor_novo=valor_novo,
                )
            )

        if buckets["ato_pai"]:
            ApostilaService._salvar_updates(ato_pai, buckets["ato_pai"])

        if buckets["detalhe"]:
            ApostilaService._salvar_updates(detalhe, buckets["detalhe"])

        ApostilaAlteracao.objects.bulk_create(registros)

    @staticmethod
    def _salvar_updates(obj: Any, updates: dict) -> None:
        """Aplica os updates em um objeto e salva em lote.

        Args:
            obj: Objeto Django cujos campos serão atualizados.
            updates: Dicionário campo-valor com as alterações.

        """
        for campo, valor in updates.items():
            setattr(obj, campo, valor)
        obj.save(update_fields=list(updates.keys()))

    @staticmethod
    def _get_detalhe(ato_pai: AtoAdministrativo) -> Any | None:
        """Retorna o detalhe associado a um ato administrativo.

        Args:
            ato_pai: Ato administrativo cujo detalhe será buscado.

        Returns:
            object | None: O detalhe associado ou None.

        """
        if ato_pai.tipo == AtoAdministrativo.Tipo.DESIGNACAO:
            return getattr(ato_pai, "designacao_detalhe", None)
        if ato_pai.tipo == AtoAdministrativo.Tipo.CESSACAO:
            return getattr(ato_pai, "cessacao_detalhe", None)
        return None
