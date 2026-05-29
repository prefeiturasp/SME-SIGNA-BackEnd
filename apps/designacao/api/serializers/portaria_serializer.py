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

    Representa portarias com informações de ato, servidor, cargo, datas,
    observações, cessacao e designacao.
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

    ano=serializers.CharField(source="ano_vigente")
    designacao = serializers.SerializerMethodField()
    cessacao = serializers.SerializerMethodField()
    tipo_insubsistencia = serializers.SerializerMethodField()
    tipo_apostila = serializers.SerializerMethodField()

 
    
    
    

    class Meta:
        model = AtoAdministrativo
        fields = [
            "id",
            "portaria",
            "doc",
            "ano",
            "tipo_de_ato",
            "nome",
            "cargo",
            "data_designacao",
            "data_cessacao",
            "numero_sei",
            "observacoes",
            "designacao",
            "cessacao",
            "tipo_insubsistencia",
            "tipo_apostila",
            "tipo"
        
        ]

    def _get_cessacao_detalhe(self, obj: AtoAdministrativo) -> Any | None:
        """Retorna o CessacaoDetalhe do ato raiz (cessação original)."""
        # Para DESIGNACAO: próprio detalhe
        if obj.tipo == AtoAdministrativo.Tipo.CESSACAO:
            return getattr(obj, "cessacao_detalhe", None)
        # Para os demais: busca no ato_raiz ou ato_pai
        pai = obj.ato_pai
        
        if pai and pai.tipo == AtoAdministrativo.Tipo.CESSACAO:
            return getattr(pai, "cessacao_detalhe", None)

        return None

    
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


    def _get_designacao_ato_administrativo(self, obj: AtoAdministrativo) -> AtoAdministrativo | None:
        """Retorna o numero_portaria do ato raiz (designação original)."""
        # Para DESIGNACAO: próprio detalhe
        if obj.tipo == AtoAdministrativo.Tipo.DESIGNACAO:
            return obj
        # Para os demais: busca no ato_raiz ou ato_pai
        raiz = obj.ato_raiz or obj.ato_pai
        if raiz:
            return raiz
        return None
        
    def _get_cessacao_ato_administrativo(self, obj: AtoAdministrativo) -> AtoAdministrativo | None:
        """Retorna os dados principais de cessação."""
        # Para CESSACAO: próprio detalhe
        if obj.tipo == AtoAdministrativo.Tipo.CESSACAO:
            return obj
        # Para os demais: busca no ato_raiz ou ato_pai
        raiz = obj.ato_raiz
        pai = obj.ato_pai
        if pai and pai.tipo == AtoAdministrativo.Tipo.CESSACAO:
            return pai
        if raiz and raiz.tipo == AtoAdministrativo.Tipo.CESSACAO:
            return raiz            
        return None


    
    def get_tipo_de_ato(self, obj: AtoAdministrativo) -> str:
        """Retorna o tipo de ato em formato legível.

        Args:
            obj: Instância de AtoAdministrativo.

        Returns:
            str: Nome legível do tipo de ato.
        """
        return obj.get_tipo_display()

     

    def get_designacao(self, obj: AtoAdministrativo) -> Any | None:
        """Retorna os dados de designação do ato administrativo atual ou do pai dele

        Args:
            obj: Instância de AtoAdministrativo.

        Returns:
            Any|None: Nome do servidor indicado ou civil.
        """
        
        detalhe = self._get_designacao_detalhe(obj)
        ato_designacao = self._get_designacao_ato_administrativo(obj)
        
        if detalhe:
            return {
                "portaria": ato_designacao.numero_portaria,
                "ano_vigente": ato_designacao.ano_vigente,
                "numero_sei": ato_designacao.sei_numero,
                "doc": ato_designacao.doc,
                "dre_nome": detalhe.dre_nome,
                "indicado_rf":detalhe.indicado_rf,                
                "indicado_vinculo": detalhe.indicado_vinculo,
                "indicado_nome_civil": detalhe.indicado_nome_civil,
                "indicado_nome_servidor": detalhe.indicado_nome_servidor,
                "indicado_lotacao": detalhe.indicado_lotacao,
                "indicado_cargo_base": detalhe.indicado_cargo_base,                
                "indicado_cargo_sobreposto":detalhe.indicado_cargo_sobreposto,
                "indicado_local_exercicio":detalhe.indicado_local_exercicio,
                "tipo_vaga": detalhe.tipo_vaga,
                "titular_nome_civil":detalhe.titular_nome_civil,
                "titular_nome_servidor": detalhe.titular_nome_servidor,
                "titular_rf": detalhe.titular_rf,
                "titular_cargo_base": detalhe.titular_cargo_base,
                "titular_vinculo": detalhe.titular_vinculo,
                "titular_tipo_vinculo": "Nao encontrado",
                "impedimento_substituicao": detalhe.impedimento_substituicao,                              
                "ue": detalhe.ue,                
                "codigo_hierarquico": detalhe.codigo_hierarquico,
                "data_inicio": detalhe.data_inicio,
                "data_fim": detalhe.data_fim,                
            }
        return None


    def get_cessacao(self, obj: AtoAdministrativo) -> Any | None:
        """Retorna os dados de cessação do ato administrativo atual ou do pai dele.

        Args:
            obj: Instância de AtoAdministrativo.

        Returns:
            str|None: Nome do servidor indicado ou civil.
        """
        
        detalhe = self._get_cessacao_detalhe(obj)
        ato_cessacao = self._get_cessacao_ato_administrativo(obj)
        
        
        if detalhe:
            return {
                "portaria": ato_cessacao.numero_portaria,
                "ano_vigente": ato_cessacao.ano_vigente,
                "numero_sei": ato_cessacao.sei_numero,
                "doc": ato_cessacao.doc,
                "remocao": detalhe.remocao,
                "a_pedido": detalhe.a_pedido,
                "aposentadoria": detalhe.aposentadoria,                
                "data_cessacao": detalhe.data_cessacao,
            }
        return None

 
    
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
            return pai.tipo
        
        return None

    def get_tipo_apostila(self, obj: AtoAdministrativo) -> str | None:
        """Retorna o tipo de apostila."""
        if obj.tipo == AtoAdministrativo.Tipo.APOSTILA:
            pai = obj.ato_pai
            return pai.tipo
        
        return None