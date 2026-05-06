from django.db.models import F
from apps.designacao.models.designacao import Designacao


class DesignacaoService:

    @staticmethod
    def get_cargos_pareados(queryset, cod1, nome1, cod2, nome2):
        """
        Retorna cargos pareados (codigo + nome), sem duplicatas por codigo,
        priorizando o último cadastrado.
        """

        def get_ultimos(qs, campo_codigo, campo_nome):
            resultado = {}
            items = (
                qs
                .filter(**{f'{campo_codigo}__isnull': False})
                .exclude(**{campo_nome: ''})
                .order_by('-id')
                .values(campo_codigo, campo_nome)
            )
            for item in items:
                codigo = item[campo_codigo]
                if codigo not in resultado:
                    resultado[codigo] = item[campo_nome]
            return resultado

        merged = get_ultimos(queryset, cod2, nome2)
        merged.update(get_ultimos(queryset, cod1, nome1))

        resultado = [
            {'codigoCargo': codigo, 'nomeCargo': nome.upper()}
            for codigo, nome in merged.items()
            if nome
        ]

        resultado.sort(key=lambda x: x['nomeCargo'])

        return resultado