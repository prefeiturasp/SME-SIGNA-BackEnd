"""Serviço de cargo base.

Contém as regras de negócio para listagem e cadastro de cargos base.
"""

from django.db.models import QuerySet

from apps.gestao.models.cargo_base import CargoBase


class CargoBaseService:
    """Serviço de negócio para manipular cargos base."""

    @staticmethod
    def listar() -> QuerySet[CargoBase]:
        """Retorna o queryset de cargos base cadastrados."""
        return CargoBase.objects.all()

    @staticmethod
    def criar(data: dict) -> CargoBase:
        """Cria um cargo base.

        Args:
            data: Dicionário com os dados validados do cargo base.

        Returns:
            CargoBase: Cargo base criado.

        """
        return CargoBase.objects.create(**data)
