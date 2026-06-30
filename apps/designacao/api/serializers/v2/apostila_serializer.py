"""Serializadores v2 para apostilas.

Define payloads de escrita e leitura de apostilas, incluindo alterações e
referência à insubsistência associada.
"""

from typing import Any

from rest_framework import serializers

from apps.designacao.api.serializers.utils import NullableDateField
from apps.designacao.models.ato_administrativo import AtoAdministrativo


class ApostilaV2AlteracaoWriteSerializer(serializers.Serializer):
    """Serializador de alteração de apostila para entrada de dados."""

    campo_alterado = serializers.CharField(max_length=100)
    valor_novo = serializers.CharField()


class ApostilaV2WriteSerializer(serializers.Serializer):
    """Serializador de escrita para apostila v2.

    Valida os campos necessários para criar uma apostila vinculada a um ato
    pai.
    """

    ato_pai = serializers.PrimaryKeyRelatedField(
        queryset=AtoAdministrativo.objects.filter(
            tipo__in=[
                AtoAdministrativo.Tipo.DESIGNACAO,
                AtoAdministrativo.Tipo.CESSACAO,
            ]
        )
    )
    sei_numero = serializers.CharField(max_length=30)
    doc = NullableDateField(required=False, default=None, allow_null=True)
    observacao = serializers.CharField()
    alteracoes = ApostilaV2AlteracaoWriteSerializer(
        many=True, required=False, default=list
    )


class ApostilaV2AlteracaoReadSerializer(serializers.Serializer):
    """Serializador de leitura para alteração de apostila."""

    campo_alterado = serializers.CharField()
    valor_anterior = serializers.CharField()
    valor_novo = serializers.CharField()


class ApostilaV2ReadSerializer(serializers.ModelSerializer):
    """Serializador de leitura para apostila v2.

    Inclui o status do ato, observação, alterações e eventual insubsistência.
    """

    status = serializers.SerializerMethodField()
    observacao = serializers.CharField(
        source="apostila_detalhe.observacao", read_only=True
    )
    alteracoes = serializers.SerializerMethodField()
    insubsistencia = serializers.SerializerMethodField()

    designacao = serializers.SerializerMethodField()
    cessacao = serializers.SerializerMethodField()

    class Meta:
        model = AtoAdministrativo
        fields = [
            "id",
            "tipo",
            "status",
            "ato_pai_id",
            "sei_numero",
            "doc",
            "criado_em",
            "observacao",
            "alteracoes",
            "insubsistencia",
            "designacao",
            "cessacao",
        ]

    def get_status(self, obj: AtoAdministrativo) -> str:
        """Retorna o status do ato de apostila.

        Args:
            obj: Instância de AtoAdministrativo.

        Returns:
            str: Status do ato.

        """
        return obj.status

    def get_alteracoes(self, obj: AtoAdministrativo) -> Any:
        """Retorna as alterações registradas na apostila.

        Args:
            obj: Instância de AtoAdministrativo.

        Returns:
            list: Lista de alterações serializadas.

        """
        try:
            qs = obj.apostila_detalhe.alteracoes.all()
            return ApostilaV2AlteracaoReadSerializer(qs, many=True).data
        except Exception:
            return []

    def get_insubsistencia(self, obj: AtoAdministrativo) -> dict | None:
        """Retorna a insubsistência ativa associada à apostila.

        Args:
            obj: Instância de AtoAdministrativo.

        Returns:
            dict|None: Dados da insubsistência ou None se não houver.

        """
        insub = next(
            (
                f
                for f in obj.filhos.all()
                if f.tipo == AtoAdministrativo.Tipo.INSUBSISTENCIA
                and f.eh_valido
            ),
            None,
        )
        if not insub:
            return None
        try:
            d = insub.insubsistencia_detalhe
            return {
                "id": insub.id,
                "sei_numero": insub.sei_numero,
                "doc": insub.doc,
                "observacoes": d.observacoes,
                "criado_em": insub.criado_em,
            }
        except Exception:
            return None

    def get_tipo_de_ato(self, obj: AtoAdministrativo) -> str:
        """Retorna o tipo de ato em formato legível.

        Args:
            obj: Instância de AtoAdministrativo.

        Returns:
            str: Nome legível do tipo de ato.

        """
        if obj.ato_pai and obj.tipo != AtoAdministrativo.Tipo.CESSACAO:
            return (
                f"{obj.get_tipo_display()} de {obj.ato_pai.get_tipo_display()}"
            )
        return f"{obj.get_tipo_display()}"

    # TODO componetizar esses métodos
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

    def _get_designacao_ato_administrativo(
        self, obj: AtoAdministrativo
    ) -> AtoAdministrativo | None:
        """Retorna o numero_portaria do ato raiz (designação original)."""
        # Para DESIGNACAO: próprio detalhe
        if obj.tipo == AtoAdministrativo.Tipo.DESIGNACAO:
            return obj
        # Para os demais: busca no ato_raiz ou ato_pai
        raiz = obj.ato_raiz or obj.ato_pai
        if raiz:
            return raiz
        return None

    def _get_cessacao_ato_administrativo(
        self, obj: AtoAdministrativo
    ) -> AtoAdministrativo | None:
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

    def get_designacao(self, obj: AtoAdministrativo) -> Any | None:
        """Retorna os dados de designação
           do ato administrativo atual ou do pai dele.

        Args:
            obj: Instância de AtoAdministrativo.

        Returns:
            Any|None: Nome do servidor indicado ou civil.

        """
        detalhe = self._get_designacao_detalhe(obj)
        ato_designacao = self._get_designacao_ato_administrativo(obj)

        if detalhe and ato_designacao is not None:
            return {
                "numero_portaria": ato_designacao.numero_portaria,
                "ano_vigente": ato_designacao.ano_vigente,
                "sei_numero": ato_designacao.sei_numero,
                "doc": ato_designacao.doc,
                "dre_nome": detalhe.dre_nome,
                "indicado_rf": detalhe.indicado_rf,
                "indicado_vinculo": detalhe.indicado_vinculo,
                "indicado_nome_civil": detalhe.indicado_nome_civil,
                "indicado_nome_servidor": detalhe.indicado_nome_servidor,
                "indicado_lotacao": detalhe.indicado_lotacao,
                "indicado_cargo_base": detalhe.indicado_cargo_base,
                "indicado_cargo_sobreposto": detalhe.indicado_cargo_sobreposto,
                "indicado_local_exercicio": detalhe.indicado_local_exercicio,
                "indicado_categoria": detalhe.indicado_categoria,
                "tipo_vaga": detalhe.tipo_vaga,
                "titular_nome_civil": detalhe.titular_nome_civil,
                "titular_nome_servidor": detalhe.titular_nome_servidor,
                "titular_rf": detalhe.titular_rf,
                "titular_cargo_base": detalhe.titular_cargo_base,
                "titular_vinculo": detalhe.titular_vinculo,
                "impedimento_substituicao": (
                    detalhe.impedimento_substituicao.descricao
                    if detalhe.impedimento_substituicao
                    else None
                ),
                "ue": detalhe.ue,
                "codigo_hierarquico": detalhe.codigo_hierarquico,
                "data_inicio": detalhe.data_inicio,
                "data_fim": detalhe.data_fim,
                "com_afastamento": detalhe.com_afastamento,
                "motivo_afastamento": (
                    detalhe.motivo_afastamento
                    if detalhe.motivo_afastamento
                    else None
                ),
                "pendencias": (
                    detalhe.pendencias if detalhe.pendencias else None
                ),
            }
        return None

    def get_cessacao(self, obj: AtoAdministrativo) -> Any | None:
        """Retorna os dados de cessação
           do ato administrativo atual ou do pai dele.

        Args:
            obj: Instância de AtoAdministrativo.

        Returns:
            str|None: Nome do servidor indicado ou civil.

        """
        detalhe = self._get_cessacao_detalhe(obj)
        ato_cessacao = self._get_cessacao_ato_administrativo(obj)

        if detalhe and ato_cessacao is not None:
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
