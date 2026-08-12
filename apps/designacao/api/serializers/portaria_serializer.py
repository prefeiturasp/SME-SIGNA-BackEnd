"""Serializador para listagem de portarias.

Fornece campos e representações customizadas para exibir portarias na tela de
publicação do Diário Oficial.
"""

import datetime

from rest_framework import serializers

from apps.designacao.api.serializers.ato_relacionado_mixin import (
    AtoRelacionadoMixin,
)
from apps.designacao.models.ato_administrativo import AtoAdministrativo


class PortariaListSerializer(AtoRelacionadoMixin, serializers.ModelSerializer):
    """Serializador de portaria para listagem.

    Representa portarias com informações de ato, servidor, cargo, datas,
    observações, cessacao e designacao.
    """

    numero_portaria = serializers.CharField()
    doc = serializers.DateField(allow_null=True)
    tipo_de_ato = serializers.SerializerMethodField()
    nome = serializers.SerializerMethodField()
    cargo = serializers.SerializerMethodField()
    data_designacao = serializers.SerializerMethodField()
    data_cessacao = serializers.SerializerMethodField()
    observacoes = serializers.SerializerMethodField()

    ano_vigente = serializers.CharField()
    designacao = serializers.SerializerMethodField()
    cessacao = serializers.SerializerMethodField()
    tipo_insubsistencia = serializers.SerializerMethodField()
    tipo_apostila = serializers.SerializerMethodField()

    class Meta:
        model = AtoAdministrativo
        fields = [
            "id",
            "numero_portaria",
            "doc",
            "ano_vigente",
            "tipo_de_ato",
            "nome",
            "cargo",
            "data_designacao",
            "data_cessacao",
            "sei_numero",
            "observacoes",
            "designacao",
            "cessacao",
            "tipo_insubsistencia",
            "tipo_apostila",
            "tipo",
        ]

    def get_nome(self, obj: AtoAdministrativo) -> str | None:
        """Retorna o nome do servidor indicado para a portaria.

        Args:
            obj: Instância de AtoAdministrativo.

        Returns:
            str|None: Nome do servidor indicado ou civil.

        """
        detalhe = self._get_designacao_detalhe(obj)

        if detalhe:
            return (
                detalhe.indicado_nome_servidor or detalhe.indicado_nome_civil
            )
        return None

    def get_cargo(self, obj: AtoAdministrativo) -> str | None:
        """Retorna o cargo associado à portaria.

        Args:
            obj: Instância de AtoAdministrativo.

        Returns:
            str|None: Cargo sobreposto ou cargo base do indicado.

        """
        detalhe = self._get_designacao_detalhe(obj)
        if detalhe:
            return (
                detalhe.indicado_cargo_sobreposto
                or detalhe.indicado_cargo_base
            )
        return None

    def get_data_designacao(
        self, obj: AtoAdministrativo
    ) -> datetime.date | None:
        """Retorna a data de início da designação.

        Args:
            obj: Instância de AtoAdministrativo.

        Returns:
            date|None: Data de início da designação.

        """
        detalhe = self._get_designacao_detalhe(obj)
        if detalhe:
            return detalhe.data_inicio
        return None

    def get_data_cessacao(
        self, obj: AtoAdministrativo
    ) -> datetime.date | None:
        """Retorna a data de cessação conforme o tipo de ato.

        Args:
            obj: Instância de AtoAdministrativo.

        Returns:
            date|None: Data de cessação para o ato ou None se não houver.

        """
        # Cessação direta no ato
        if obj.tipo == AtoAdministrativo.Tipo.CESSACAO:
            cessacao = getattr(obj, "cessacao_detalhe", None)
            if cessacao:
                return cessacao.data_cessacao
        # Busca cessação ativa nos filhos (para designações)
        if obj.tipo == AtoAdministrativo.Tipo.DESIGNACAO:
            detalhe = getattr(obj, "designacao_detalhe", None)
            if detalhe:
                return detalhe.data_fim
        return None

    def get_observacoes(self, obj: AtoAdministrativo) -> str | None:
        """Retorna observações específicas por tipo de ato."""
        if obj.tipo == AtoAdministrativo.Tipo.INSUBSISTENCIA:
            insubsistencia = getattr(obj, "insubsistencia_detalhe", None)
            return getattr(insubsistencia, "observacoes", None)
        if obj.tipo == AtoAdministrativo.Tipo.APOSTILA:
            apostila = getattr(obj, "apostila_detalhe", None)
            return getattr(apostila, "observacao", None)
        return None

    def get_tipo_insubsistencia(self, obj: AtoAdministrativo) -> str | None:
        """Retorna o tipo de insubsistência se designação ou cessação."""
        if obj.tipo == AtoAdministrativo.Tipo.INSUBSISTENCIA:
            pai = obj.ato_pai
            if pai is not None:
                return pai.tipo

        return None

    def get_tipo_apostila(self, obj: AtoAdministrativo) -> str | None:
        """Retorna o tipo de apostila."""
        if obj.tipo == AtoAdministrativo.Tipo.APOSTILA:
            pai = obj.ato_pai
            if pai is not None:
                return pai.tipo

        return None

    def get_tipo_de_ato(self, obj: AtoAdministrativo) -> str:
        """Retorna o tipo de ato em formato legível.

        Args:
            obj: Instância de AtoAdministrativo.

        Returns:
            str: Nome legível do tipo de ato.

        """
        if obj.ato_pai and obj.tipo != AtoAdministrativo.Tipo.CESSACAO:
            if (
                obj.tipo == AtoAdministrativo.Tipo.INSUBSISTENCIA
                and obj.ato_pai.tipo == AtoAdministrativo.Tipo.INSUBSISTENCIA
            ):
                return "Tornar sem efeito"
            if (
                obj.tipo == AtoAdministrativo.Tipo.INSUBSISTENCIA
                and obj.ato_pai.tipo == AtoAdministrativo.Tipo.APOSTILA
            ):
                return "Anulação de Apostila"
            return (
                f"{obj.get_tipo_display()} de {obj.ato_pai.get_tipo_display()}"
            )
        return f"{obj.get_tipo_display()}"
