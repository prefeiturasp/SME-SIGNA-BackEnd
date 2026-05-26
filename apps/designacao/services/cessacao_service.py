from django.db import transaction
from rest_framework.exceptions import ValidationError

from apps.designacao.models.ato_administrativo import AtoAdministrativo
from apps.designacao.models.cessacao_detalhe import CessacaoDetalhe


_CAMPOS_ATO = frozenset({"numero_portaria", "ano_vigente", "sei_numero", "doc"})


class CessacaoService:

    @classmethod
    def criar(cls, data: dict) -> AtoAdministrativo:
        ato_pai: AtoAdministrativo = data["ato_pai"]

        if not ato_pai.eh_valido:
            raise ValidationError({"ato_pai": "Esta designação está insubsistente."})

        if ato_pai.filhos.filter(
            tipo=AtoAdministrativo.Tipo.CESSACAO, ativo=True
        ).exists():
            raise ValidationError(
                {"ato_pai": "Esta designação já possui uma cessação ativa."}
            )

        data_ato = {k: v for k, v in data.items() if k in _CAMPOS_ATO}
        data_detalhe = {
            k: v for k, v in data.items() if k not in _CAMPOS_ATO and k != "ato_pai"
        }

        with transaction.atomic():
            ato = AtoAdministrativo.objects.create(
                tipo=AtoAdministrativo.Tipo.CESSACAO,
                ato_pai=ato_pai,
                **data_ato,
            )
            CessacaoDetalhe.objects.create(ato=ato, **data_detalhe)

        return ato
