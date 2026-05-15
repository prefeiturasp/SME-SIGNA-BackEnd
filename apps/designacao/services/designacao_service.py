from django.db import transaction
from django.db.models import F

from apps.designacao.models.ato_administrativo import AtoAdministrativo
from apps.designacao.models.designacao_detalhe import DesignacaoDetalhe

_CAMPOS_ATO = frozenset({"numero_portaria", "ano_vigente", "sei_numero", "doc"})


class DesignacaoService:

    @classmethod
    def criar(cls, data: dict) -> AtoAdministrativo:
        data_ato = {k: v for k, v in data.items() if k in _CAMPOS_ATO}
        data_detalhe = {k: v for k, v in data.items() if k not in _CAMPOS_ATO}

        with transaction.atomic():
            ato = AtoAdministrativo.objects.create(
                tipo=AtoAdministrativo.Tipo.DESIGNACAO,
                **data_ato,
            )
            DesignacaoDetalhe.objects.create(ato=ato, **data_detalhe)

        return ato

    @staticmethod
    def atualizar(ato: AtoAdministrativo, data: dict) -> AtoAdministrativo:
        data_ato = {k: v for k, v in data.items() if k in _CAMPOS_ATO}
        data_detalhe = {k: v for k, v in data.items() if k not in _CAMPOS_ATO}

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
    def get_cargos_pareados(
        queryset,
        cod1: str,
        nome1: str,
        cod2: str,
        nome2: str,
    ) -> list:
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
