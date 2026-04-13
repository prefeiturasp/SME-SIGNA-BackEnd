from django.db.models import F
from apps.designacao.models.designacao import Designacao


class DesignacaoService:

    @staticmethod
    def get_cargos_pareados(queryset, cod1, nome1, cod2, nome2):
        """
        Retorna cargos pareados (codigo + nome).
        """

        qs1 = queryset.values(
            codigo=F(cod1),
            nome=F(nome1),
        ).filter(
            **{f"{cod1}__isnull": False}
        ).exclude(
            **{nome1: ""}
        )

        qs2 = queryset.values(
            codigo=F(cod2),
            nome=F(nome2),
        ).filter(
            **{f"{cod2}__isnull": False}
        ).exclude(
            **{nome2: ""}
        )

        pares = qs1.union(qs2)

        resultado = [
            {
                "codigoCargo": item["codigo"],
                "nomeCargo": item["nome"],
            }
            for item in pares
            if item["nome"]
        ]

        resultado.sort(key=lambda x: x["nomeCargo"])

        return resultado