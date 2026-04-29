from rest_framework.exceptions import ValidationError
from apps.designacao.models.apostila import Apostila
from apps.designacao.models.designacao import Designacao


class ApostilaService:

    @staticmethod
    def criar_apostila(data):

        designacao_id = data.pop("designacao")
        ato_apostilado = data.pop("ato_apostilado")

        designacao = Designacao.objects.filter(
            id=designacao_id,
            is_deleted=False
        ).select_related("cessacao").first()

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

        if alvo.is_deleted:
            raise ValidationError("Não é possível apostilar um ato deletado.")

        queryset = Apostila.objects.filter(
            is_deleted=False,
            tipo=Apostila.Tipo.APOSTILA
        )

        if alvo_designacao:
            queryset = queryset.filter(designacao=alvo_designacao)
        else:
            queryset = queryset.filter(cessacao=alvo_cessacao)

        apostilas_ativas = queryset.exclude(
            id__in=Apostila.objects.filter(
                tipo=Apostila.Tipo.ANULACAO,
                apostila_referencia__in=queryset
            ).values_list("apostila_referencia_id", flat=True)
        )

        if apostilas_ativas.exists():
            raise ValidationError(
                "Já existe uma apostila válida para este ato."
            )

        return Apostila.objects.create(
            tipo=data.get("tipo"),
            designacao=alvo_designacao,
            cessacao=alvo_cessacao,
            sei_numero=data.get("sei_numero"),
            observacao=data.get("observacao"),
            d_o=data.get("d_o", "")
        )