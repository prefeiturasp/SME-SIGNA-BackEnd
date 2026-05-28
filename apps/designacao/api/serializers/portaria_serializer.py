"""Serializador para listagem de portarias.

Fornece campos e representações customizadas para exibir portarias na tela de
publicação do Diário Oficial.
"""

import datetime
from typing import Any

from rest_framework import serializers

from apps.designacao.models.ato_administrativo import AtoAdministrativo


class PortariaListSerializer(serializers.ModelSerializer):
    """Serializador de portaria para listagem.

    Representa portarias com informações de ato, servidor, cargo, datas e
    observações.
    """

    portaria = serializers.CharField(source="numero_portaria")
    doc = serializers.DateField(allow_null=True)
    tipo_de_ato = serializers.SerializerMethodField()
    nome = serializers.SerializerMethodField()
    cargo = serializers.SerializerMethodField()
    data_designacao = serializers.SerializerMethodField()
    data_cessacao = serializers.SerializerMethodField()
    numero_sei = serializers.CharField(source="sei_numero")
    observacoes = serializers.SerializerMethodField()

    class Meta:
        model = AtoAdministrativo
        fields = [
            "id",
            "portaria",
            "doc",
            "tipo_de_ato",
            "nome",
            "cargo",
            "data_designacao",
            "data_cessacao",
            "numero_sei",
            "observacoes",
        ]

    def _get_designacao_detalhe(self, obj: AtoAdministrativo) -> Any | None:
        """Retorna o DesignacaoDetalhe do ato raiz (designação original)."""
        # Para DESIGNACAO: próprio detalhe
        if obj.tipo == AtoAdministrativo.Tipo.DESIGNACAO:
            return getattr(obj, "designacao_detalhe", None)
        # Para os demais: busca no ato_raiz ou ato_pai
        raiz = obj.ato_raiz or obj.ato_pai
        if raiz:
            return getattr(raiz, "designacao_detalhe", None)
        return None

    def get_tipo_de_ato(self, obj: AtoAdministrativo) -> str:
        """Retorna o tipo de ato em formato legível.

        Args:
            obj: Instância de AtoAdministrativo.

        Returns:
            str: Nome legível do tipo de ato.
        """
        return obj.get_tipo_display()

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
