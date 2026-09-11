"""Serviço de modelo de portaria.

Contém as regras de negócio para listagem e cadastro de modelos de
texto de portaria.
"""

from django.db.models import QuerySet

from apps.gestao.models.modelo_portaria import ModeloPortaria


class ModeloPortariaService:
    """Serviço de negócio para manipular modelos de portaria."""

    @staticmethod
    def listar() -> QuerySet[ModeloPortaria]:
        """Retorna o queryset de modelos de portaria cadastrados."""
        return ModeloPortaria.objects.all()

    @staticmethod
    def criar(data: dict) -> ModeloPortaria:
        """Cria um modelo de portaria.

        Args:
            data: Dicionário com os dados validados do modelo de portaria.

        Returns:
            ModeloPortaria: Modelo de portaria criado.

        """
        return ModeloPortaria.objects.create(**data)
