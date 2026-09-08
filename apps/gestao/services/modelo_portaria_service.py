"""Serviço de modelo de portaria.

Contém as regras de negócio para listagem, cadastro e resolução do
modelo vigente de texto de portaria.
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
    def resolver_ativo(
        tipo_portaria: str, tipo_ato_pai: str = ""
    ) -> ModeloPortaria | None:
        """Resolve o modelo de portaria ativo para um tipo de ato.

        Por enquanto não existe nada que impeça dois modelos ativos
        para a mesma combinação de tipo — se acontecer, pega o mais
        recente. Também não diferencia por ato específico (ex.: por
        cargo) dentro do mesmo tipo ainda; isso fica para uma evolução
        futura deste serviço.

        Args:
            tipo_portaria: Tipo do ato ao qual o texto se refere
                (designação, cessação, apostila ou insubsistência).
            tipo_ato_pai: Tipo do ato pai, aplicável apenas quando o
                texto varia conforme a origem (apostila/insubsistência).

        Returns:
            ModeloPortaria | None: Modelo ativo mais recente para a
            combinação informada, ou None se não houver nenhum.

        """
        return (
            ModeloPortaria.objects.filter(
                tipo_portaria=tipo_portaria,
                tipo_ato_pai=tipo_ato_pai,
                status=ModeloPortaria.Status.ATIVO,
            )
            .order_by("-criado_em")
            .first()
        )

    @staticmethod
    def criar(data: dict) -> ModeloPortaria:
        """Cria um modelo de portaria.

        Args:
            data: Dicionário com os dados validados do modelo de portaria.

        Returns:
            ModeloPortaria: Modelo de portaria criado.

        """
        return ModeloPortaria.objects.create(**data)
