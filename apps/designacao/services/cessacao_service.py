"""Serviço de cessação.

Contém a lógica para criar atos administrativos de cessação e seus detalhes
associados, garantindo validações de estados de designação.
"""

from django.db import transaction
from django.db.models import QuerySet
from rest_framework.exceptions import ValidationError

from apps.designacao.models.ato_administrativo import AtoAdministrativo
from apps.designacao.models.cessacao_detalhe import CessacaoDetalhe

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


class CessacaoService:
    """Serviço de negócio para criar cessações."""

    # ── Querysets ────────────────────────────────────────────────────────────

    @staticmethod
    def listar() -> QuerySet:
        """Retorna queryset de cessações (AtoAdministrativo)."""
        return (
            AtoAdministrativo.objects.filter(
                tipo=AtoAdministrativo.Tipo.CESSACAO
            )
            .select_related("cessacao_detalhe")
            .prefetch_related(
                "filhos",
                "filhos__apostila_detalhe",
                "filhos__insubsistencia_detalhe",
            )
            .order_by("-criado_em")
        )

    @staticmethod
    def buscar(pk: int) -> AtoAdministrativo | None:
        """Retorna uma cessação por pk."""
        return (
            AtoAdministrativo.objects.filter(
                tipo=AtoAdministrativo.Tipo.CESSACAO
            )
            .select_related("cessacao_detalhe")
            .prefetch_related(
                "filhos",
                "ato_pai__designacao_detalhe",
                "filhos__apostila_detalhe",
                "filhos__insubsistencia_detalhe",
            )
            .order_by("-criado_em")
            .filter(pk=pk)
            .first()
        )

    @classmethod
    def criar(cls, data: dict) -> AtoAdministrativo:
        """Cria um ato administrativo de cessação.

        Args:
            data: Dicionário com os dados do ato e detalhe de cessação.

        Returns:
            AtoAdministrativo: Ato administrativo de cessação criado.

        Raises:
            ValidationError: Se o ato pai não for válido ou já tiver cessação
            ativa.

        """
        ato_pai: AtoAdministrativo = data["ato_pai"]

        if not ato_pai.eh_valido:
            raise ValidationError(
                {"ato_pai": "Esta designação está insubsistente."}
            )

        if ato_pai.filhos.filter(
            tipo=AtoAdministrativo.Tipo.CESSACAO, ativo=True
        ).exists():
            raise ValidationError(
                {"ato_pai": "Esta designação já possui uma cessação ativa."}
            )

        data_ato = {k: v for k, v in data.items() if k in _CAMPOS_ATO}
        data_detalhe = {
            k: v
            for k, v in data.items()
            if k not in _CAMPOS_ATO and k != "ato_pai"
        }

        with transaction.atomic():
            ato = AtoAdministrativo.objects.create(
                tipo=AtoAdministrativo.Tipo.CESSACAO,
                status_publicacao=AtoAdministrativo.StatusPublicacao.NAO_PUBLICADO,
                ato_pai=ato_pai,
                **data_ato,
            )
            CessacaoDetalhe.objects.create(ato=ato, **data_detalhe)

        return ato

    @staticmethod
    def atualizar(ato: AtoAdministrativo, data: dict) -> AtoAdministrativo:
        """Atualiza um ato administrativo de cessação e seu detalhe.

        Args:
            ato: Ato administrativo de cessação existente.
            data: Dicionário com os campos a atualizar.

        Returns:
            AtoAdministrativo: Ato administrativo atualizado.

        Raises:
            ValidationError: Se o ato pai não for válido.
            ValidationError: Se a cessação não possui uma designação pai.
            ValidationError: Se a cessação estiver publicada.

        """
        ato_pai: AtoAdministrativo | None = ato.ato_pai

        if ato_pai is None:
            raise ValidationError(
                {"ato_pai": "Esta cessação não possui uma designação pai."}
            )

        if ato_pai and not ato_pai.eh_valido:
            raise ValidationError(
                {"ato_pai": "Esta designação está insubsistente."}
            )

        if (
            ato.status_publicacao
            == AtoAdministrativo.StatusPublicacao.PUBLICADO
        ):
            raise ValidationError(
                {
                    "ato": (
                        "Esta cessação não pode "
                        "ser atualizada pois está publicada."
                    )
                }
            )

        data_ato = {k: v for k, v in data.items() if k in _CAMPOS_ATO}
        data_detalhe = {
            k: v
            for k, v in data.items()
            if k not in _CAMPOS_ATO and k != "ato_pai"
        }

        with transaction.atomic():
            if data_ato:
                for field, value in data_ato.items():
                    setattr(ato, field, value)
                ato.save(update_fields=list(data_ato.keys()))

            if data_detalhe:
                detalhe = ato.cessacao_detalhe
                for field, value in data_detalhe.items():
                    setattr(detalhe, field, value)
                detalhe.save(update_fields=list(data_detalhe.keys()))

        return ato
