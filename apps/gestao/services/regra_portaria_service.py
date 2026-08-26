"""Serviço de regra de portaria.

Contém as regras de negócio para listagem, cadastro e edição de regras
de portaria.
"""

from django.db.models import QuerySet

from apps.gestao.models.regra_portaria import RegraPortaria


class RegraPortariaService:
    """Serviço de negócio para manipular regras de portaria."""

    @staticmethod
    def listar() -> QuerySet[RegraPortaria]:
        """Retorna o queryset de regras de portaria cadastradas."""
        return RegraPortaria.objects.all()

    @staticmethod
    def criar(data: dict) -> RegraPortaria:
        """Cria uma regra de portaria.

        Args:
            data: Dicionário com os dados validados da regra de portaria.

        Returns:
            RegraPortaria: Regra de portaria criada.

        """
        return RegraPortaria.objects.create(**data)

    @staticmethod
    def atualizar(regra: RegraPortaria, data: dict) -> RegraPortaria:
        """Atualiza os dados de uma regra de portaria existente.

        Args:
            regra: Regra de portaria a ser atualizada.
            data: Dicionário com os dados validados para atualização.

        Returns:
            RegraPortaria: Regra de portaria atualizada.

        """
        for campo, valor in data.items():
            setattr(regra, campo, valor)
        regra.save()
        return regra
