"""Serializadores legados para designação e impedimentos.

Fornece serialização de designações legadas com detalhes de cessação,
insubsistência
apositilas e impedimentos de substituição.
"""

from typing import Any

from rest_framework import serializers

from apps.designacao.api.serializers.apostila_serializer import (
    ApostilaSerializer,
)
from apps.designacao.api.serializers.cessacao_serializer import (
    CessacaoSerializer,
)
from apps.designacao.api.serializers.insubsistencia_serializer import (
    InsubsistenciaSerializer,
)
from apps.designacao.models.designacao import (
    Designacao,
    ImpedimentoSubstituicao,
)


class ImpedimentoSubstituicaoLegadoSerializer(serializers.ModelSerializer):
    """Serializador para impedimentos de substituição legados.

    Serializa informações básicas de impedimentos de substituição
    utilizadas pela API legada, incluindo identificador, código
    e descrição do impedimento.
    """

    class Meta:
        model = ImpedimentoSubstituicao
        fields = ["id", "codigo", "descricao"]


class DesignacaoLegadoSerializer(serializers.ModelSerializer):
    """Serializador para designações legadas.

    Une dados de designação com cessação, insubsistência, apostilas e
    informações
    de impedimento de substituição para a API legada.
    """

    cessacao = serializers.SerializerMethodField()
    insubsistencia = serializers.SerializerMethodField()
    apostilas = serializers.SerializerMethodField()

    # Campos opcionais que o model não declara blank=True mas o frontend não envia  # noqa: E501
    ue = serializers.CharField(
        max_length=50, required=False, default="", allow_blank=True
    )
    dre = serializers.CharField(
        max_length=50, required=False, default="", allow_blank=True
    )
    funcionarios_da_unidade = serializers.CharField(
        max_length=50, required=False, default="", allow_blank=True
    )
    doc = serializers.CharField(
        max_length=100, required=False, default="", allow_blank=True
    )

    impedimento_substituicao = serializers.PrimaryKeyRelatedField(
        queryset=ImpedimentoSubstituicao.objects.all(),
        required=False,
        allow_null=True,
    )
    impedimento_substituicao_detail = ImpedimentoSubstituicaoLegadoSerializer(
        source="impedimento_substituicao",
        read_only=True,
    )
    impedimento_display = serializers.SerializerMethodField()

    tipo_vaga_display = serializers.CharField(
        source="get_tipo_vaga_display", read_only=True
    )
    cargo_vaga_display = serializers.CharField(
        source="get_cargo_vaga_display", read_only=True
    )

    class Meta:
        model = Designacao
        fields = "__all__"

    def get_cessacao(self, obj: Designacao) -> dict | None:
        """Retorna os dados de cessação associados à designação.

        Args:
            obj: Instância de Designacao.

        Returns:
            dict|None: Dados serializados da cessação ou None se não existir.
        """
        try:
            cessacao = obj.cessacao
            if cessacao and not cessacao.is_deleted:
                return CessacaoSerializer(cessacao).data
        except Exception:
            pass
        return None

    def get_insubsistencia(self, obj: Designacao) -> dict | None:
        """Retorna a insubsistência mais recente vinculada à designação.

        Args:
            obj: Instância de Designacao.

        Returns:
            dict|None: Dados serializados da insubsistência ou None se não
            existir.
        """
        insubs_qs = getattr(obj, "insubsistencia", None)
        if not insubs_qs:
            return None

        insubsistencia = (
            insubs_qs.filter(is_deleted=False).order_by("-criado_em").first()
        )
        if insubsistencia:
            return InsubsistenciaSerializer(insubsistencia).data
        return None

    def get_apostilas(self, obj: Designacao) -> Any:
        """Retorna as apostilas associadas à designação.

        Args:
            obj: Instância de Designacao.

        Returns:
            list: Lista de apostilas serializadas.
        """
        apostilas = obj.apostilas.filter(is_deleted=False).order_by(
            "-criado_em"
        )
        return ApostilaSerializer(apostilas, many=True).data

    def get_impedimento_display(self, obj: Designacao) -> str | None:
        """Retorna a descrição do impedimento de substituição.

        Args:
            obj: Instância de Designacao.

        Returns:
            str|None: Descrição do impedimento ou None se não existir.
        """
        if obj.impedimento_substituicao:
            return obj.impedimento_substituicao.descricao
        return None

    def update(self, instance: Designacao, validated_data: dict) -> Designacao:
        """Atualiza a instância de designação ignorando campos imutáveis.

        Args:
            instance: Instância de Designacao a ser atualizada.
            validated_data: Dados validados para atualização.

        Returns:
            Designacao: Instância atualizada.
        """
        for field in ("is_deleted", "deleted_at", "criado_em", "id"):
            validated_data.pop(field, None)
        return super().update(instance, validated_data)
