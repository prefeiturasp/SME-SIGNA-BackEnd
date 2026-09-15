"""Serviço de insubsistência de atos administrativos.

Fornece lógica para criar insubsistências, reverter apostilas e manter a
consistência dos atos administrativos relacionados.
"""

from django.db import transaction
from django.db.models import Model, QuerySet
from rest_framework.exceptions import ValidationError

from apps.designacao.models.ato_administrativo import AtoAdministrativo
from apps.designacao.models.insubsistencia_apostila_detalhe import (
    InsubsistenciaApostilaDetalhe,
)
from apps.designacao.models.insubsistencia_detalhe import InsubsistenciaDetalhe

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


def _filhos_ativos_ids(
    ato_pai: AtoAdministrativo, tipo_filho: str
) -> list[int]:
    """Retorna IDs de filhos ativos de um ato administrativo.

    Args:
        ato_pai: Ato administrativo pai.
        tipo_filho: Tipo de ato filho desejado.

    Returns:
        list[int]: Lista de IDs dos atos filhos ativos.

    """
    return list(
        ato_pai.filhos.filter(tipo=tipo_filho, ativo=True).values_list(
            "pk", flat=True
        )
    )


class InsubsistenciaService:
    """Serviço para a criação e reversão de insubsistências."""

    # ── Querysets ────────────────────────────────────────────────────────────

    @staticmethod
    def listar() -> QuerySet:
        """Retorna queryset de insubsistências (AtoAdministrativo)."""
        return (
            AtoAdministrativo.objects.filter(
                tipo=AtoAdministrativo.Tipo.INSUBSISTENCIA
            )
            .select_related(
                "insubsistencia_detalhe",
                "insubsistencia_apostila_detalhe",
                "ato_pai__designacao_detalhe",
                "ato_raiz__designacao_detalhe",
                "ato_pai__cessacao_detalhe",
            )
            .order_by("-criado_em")
        )

    @staticmethod
    def buscar(pk: int) -> AtoAdministrativo | None:
        """Retorna uma insubsistência por pk."""
        return InsubsistenciaService.listar().filter(pk=pk).first()

    @staticmethod
    def excluir(instancia: AtoAdministrativo) -> None:
        """Remove a insubsistência e reativa o ato pai associado.

        Args:
            instancia: Ato de insubsistência a ser removido.

        """
        ato_pai = instancia.ato_pai
        if ato_pai:
            ato_pai.ativo = True
            ato_pai.save(update_fields=["ativo"])
        instancia.delete()

    @staticmethod
    def criar(data: dict) -> AtoAdministrativo:
        """Cria um ato de insubsistência para um ato administrativo existente.

        Args:
            data: Dicionário com os dados necessários para a
            insubsistência, incluindo 'ato_pai'.

        Returns:
            AtoAdministrativo: O novo ato de insubsistência criado.

        Raises:
            ValidationError: Se o ato pai já estiver insubsistente ou
            já possuir uma insubsistência ativa.

        """
        ato_pai: AtoAdministrativo = data["ato_pai"]

        if not ato_pai.eh_valido:
            raise ValidationError(
                {"ato_pai": "Este ato já está insubsistente."}
            )

        if ato_pai.filhos.filter(
            tipo=AtoAdministrativo.Tipo.INSUBSISTENCIA, ativo=True
        ).exists():
            raise ValidationError(
                {"ato_pai": "Este ato já possui uma insubsistência ativa."}
            )

        data_ato = {k: v for k, v in data.items() if k in _CAMPOS_ATO}
        observacoes = data.get("observacoes", "")

        texto_apostila = data.get("texto_apostila", "")

        with transaction.atomic():
            ato = AtoAdministrativo.objects.create(
                tipo=AtoAdministrativo.Tipo.INSUBSISTENCIA,
                status_publicacao=AtoAdministrativo.StatusPublicacao.NAO_PUBLICADO,
                ato_pai=ato_pai,
                **data_ato,
            )
            InsubsistenciaDetalhe.objects.create(
                ato=ato, observacoes=observacoes
            )

            if ato_pai.tipo == AtoAdministrativo.Tipo.APOSTILA:
                InsubsistenciaApostilaDetalhe.objects.create(
                    ato=ato, texto=texto_apostila
                )

            ato_pai.ativo = False
            ato_pai.save(update_fields=["ativo"])

            tipo_pai = ato_pai.tipo

            if (
                tipo_pai == AtoAdministrativo.Tipo.INSUBSISTENCIA
                and ato_pai.ato_pai_id
            ):
                # TSE: insubsistindo uma Insubsistência — restaura o ato original  # noqa: E501
                avo = ato_pai.ato_pai
                if avo is not None:
                    avo.ativo = True
                    avo.save(update_fields=["ativo"])

            elif tipo_pai == AtoAdministrativo.Tipo.APOSTILA:
                InsubsistenciaService._reverter_apostila(ato_pai)

            elif tipo_pai in (
                AtoAdministrativo.Tipo.DESIGNACAO,
                AtoAdministrativo.Tipo.CESSACAO,
            ):
                ids_ativos = _filhos_ativos_ids(
                    ato_pai, AtoAdministrativo.Tipo.APOSTILA
                )
                apostilas_validas = AtoAdministrativo.objects.filter(
                    pk__in=ids_ativos
                ).prefetch_related("apostila_detalhe__alteracoes")

                for apostila in apostilas_validas:
                    InsubsistenciaService._reverter_apostila(apostila)
                    apostila.ativo = False
                    apostila.save(update_fields=["ativo"])

        return ato

    @staticmethod
    def _reverter_apostila(apostila_ato: AtoAdministrativo) -> None:
        """Reverte as alterações de uma apostila nos atos que ela afetou.

        Cada `ApostilaAlteracao` registra o ato administrativo em que foi
        de fato aplicada (`ato_alterado`) — normalmente o próprio ato
        apostilado, mas, no caso de uma apostila sobre uma cessação, pode
        também ser a designação de origem dela (`tipo_ato_alvo="DESIGNACAO"`
        na criação). A reversão precisa respeitar o `ato_alterado` de cada
        alteração individualmente, em vez de assumir um único ato de
        destino — do contrário, alterações aplicadas num ato diferente do
        destino assumido são silenciosamente descartadas.

        Args:
            apostila_ato: Ato administrativo do tipo apostila que será
            revertido.

        """
        try:
            alteracoes = list(
                apostila_ato.apostila_detalhe.alteracoes.select_related(
                    "ato_alterado"
                )
            )
        except Exception:
            return

        if not alteracoes:
            return

        atos_por_pk: dict[int, AtoAdministrativo] = {}
        detalhes_por_pk: dict[int, Model | None] = {}
        ato_updates_por_pk: dict[int, dict] = {}
        detalhe_updates_por_pk: dict[int, dict] = {}

        for alt in alteracoes:
            alvo = alt.ato_alterado
            atos_por_pk[alvo.pk] = alvo

            if alvo.pk not in detalhes_por_pk:
                detalhes_por_pk[alvo.pk] = InsubsistenciaService._get_detalhe(
                    alvo
                )
            detalhe_alvo = detalhes_por_pk[alvo.pk]

            campo = alt.campo_alterado
            valor = InsubsistenciaService._coerce_valor(
                alvo, detalhe_alvo, campo, alt.valor_anterior
            )

            if hasattr(alvo, campo):
                ato_updates_por_pk.setdefault(alvo.pk, {})[campo] = valor
            elif (
                detalhe_alvo
                and hasattr(detalhe_alvo, campo)
                and campo not in ("ato_id", "ato")
            ):
                detalhe_updates_por_pk.setdefault(alvo.pk, {})[campo] = valor

        for pk, updates in ato_updates_por_pk.items():
            alvo = atos_por_pk[pk]
            for campo, valor in updates.items():
                setattr(alvo, campo, valor)
            alvo.save(update_fields=list(updates.keys()))

        for pk, updates in detalhe_updates_por_pk.items():
            detalhe_alvo = detalhes_por_pk[pk]
            assert detalhe_alvo is not None
            for campo, valor in updates.items():
                setattr(detalhe_alvo, campo, valor)
            detalhe_alvo.save(update_fields=list(updates.keys()))

    @staticmethod
    def _get_detalhe(ato: AtoAdministrativo) -> Model | None:
        """Retorna o detalhe associado a um ato administrativo, se houver."""
        if ato.tipo == AtoAdministrativo.Tipo.DESIGNACAO:
            return getattr(ato, "designacao_detalhe", None)
        if ato.tipo == AtoAdministrativo.Tipo.CESSACAO:
            return getattr(ato, "cessacao_detalhe", None)
        return None

    @staticmethod
    def _coerce_valor(
        ato: AtoAdministrativo,
        detalhe: Model | None,
        campo: str,
        valor_str: str,
    ) -> str | bool | int | float | None:
        """Converta o valor de string para o tipo de campo apropriado.

        Args:
            ato: Instância do ato administrativo alvo.
            detalhe: Instância do detalhe associado ao ato, se existir.
            campo: Nome do campo a ser convertido.
            valor_str: Valor original em string.

        Returns:
            Valor convertido para o tipo do campo, ou valor original se
            a conversão falhar.

        """
        from django.db.models import BooleanField, FloatField, IntegerField

        try:
            if hasattr(ato, campo):
                field = ato._meta.get_field(campo)
            elif detalhe and hasattr(detalhe, campo):
                field = detalhe._meta.get_field(campo)
            else:
                return valor_str

            if valor_str == "" and getattr(field, "null", False):
                return None

            if isinstance(field, BooleanField):
                return valor_str in (True, "True", "true", "1", 1)

            if isinstance(field, IntegerField):
                return int(valor_str) if valor_str not in ("", None) else None

            if isinstance(field, FloatField):
                return (
                    float(valor_str) if valor_str not in ("", None) else None
                )

        except Exception:
            pass
        return valor_str
