from rest_framework import serializers

from apps.designacao.models.ato_administrativo import AtoAdministrativo


class PortariaListSerializer(serializers.ModelSerializer):
    """Serializer para a listagem de portarias na tela de publicação D.O.

    Colunas:
        PORTARIA | DOC | TIPO DE ATO | NOME | CARGO | D.O |
        DATA DA DESIGNAÇÃO | DATA DA CESSAÇÃO | Nº SEI
    """

    portaria = serializers.CharField(source="numero_portaria")
    doc = serializers.CharField()
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

    def _get_designacao_detalhe(self, obj):
        """Retorna o DesignacaoDetalhe do ato raiz (designação original)."""
        # Para DESIGNACAO: próprio detalhe
        if obj.tipo == AtoAdministrativo.Tipo.DESIGNACAO:
            return getattr(obj, "designacao_detalhe", None)
        # Para os demais: busca no ato_raiz ou ato_pai
        raiz = obj.ato_raiz or obj.ato_pai
        if raiz:
            return getattr(raiz, "designacao_detalhe", None)
        return None

    def get_tipo_de_ato(self, obj):
        return obj.get_tipo_display()

    def get_nome(self, obj):
        detalhe = self._get_designacao_detalhe(obj)
        if detalhe:
            return detalhe.indicado_nome_servidor or detalhe.indicado_nome_civil
        return None

    def get_cargo(self, obj):
        detalhe = self._get_designacao_detalhe(obj)
        if detalhe:
            return detalhe.indicado_cargo_sobreposto or detalhe.indicado_cargo_base
        return None

    def get_data_designacao(self, obj):
        detalhe = self._get_designacao_detalhe(obj)
        if detalhe:
            return detalhe.data_inicio
        return None

    def get_data_cessacao(self, obj):
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

    def get_observacoes(self, obj):
        """Retorna observações específicas por tipo de ato."""
        if obj.tipo == AtoAdministrativo.Tipo.INSUBSISTENCIA:
            insubsistencia = getattr(obj, "insubsistencia_detalhe", None)
            return getattr(insubsistencia, "observacoes", None)
        if obj.tipo == AtoAdministrativo.Tipo.APOSTILA:
            apostila = getattr(obj, "apostila_detalhe", None)
            return getattr(apostila, "observacao", None)
        return None
