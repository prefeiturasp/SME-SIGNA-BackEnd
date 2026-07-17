"""Serializadores para cessação.

Inclui payloads de criação e leitura de cessação, com validações de número e
ano.
"""

from rest_framework import serializers

from apps.designacao.api.serializers.ato_relacionado_mixin import (
    AtoRelacionadoMixin,
)
from apps.designacao.api.serializers.utils import (
    NullableDateField,
    validar_somente_numeros,
)
from apps.designacao.models.ato_administrativo import AtoAdministrativo


class CessacaoWriteSerializer(serializers.Serializer):
    """Serializador de escrita para cessação.

    Valida os dados necessários para criar uma cessação vinculada a uma
    designação.
    """

    # AtoAdministrativo pai (designação à qual esta cessação pertence)
    ato_pai = serializers.PrimaryKeyRelatedField(
        queryset=AtoAdministrativo.objects.filter(
            tipo=AtoAdministrativo.Tipo.DESIGNACAO
        )
    )

    # Campos de AtoAdministrativo
    numero_portaria = serializers.CharField(max_length=20)
    ano_vigente = serializers.CharField(max_length=6)
    sei_numero = serializers.CharField(max_length=30)
    doc = NullableDateField(required=False, default=None, allow_null=True)

    # Campos de CessacaoDetalhe
    a_pedido = serializers.BooleanField(required=False, default=False)
    remocao = serializers.BooleanField(required=False, default=False)
    aposentadoria = serializers.BooleanField(required=False, default=False)
    data_cessacao = serializers.DateField()

    def validate_numero_portaria(self, value: str) -> str:
        """Valida que o número da portaria contenha apenas dígitos.

        Args:
            value: Valor do número da portaria.

        Returns:
            str: Valor validado com apenas dígitos.

        """
        return validar_somente_numeros(value)

    def validate_ano_vigente(self, value: str) -> str:
        """Valida que o ano vigente contenha apenas dígitos.

        Args:
            value: Valor do ano vigente.

        Returns:
            str: Valor validado com apenas dígitos.

        """
        return validar_somente_numeros(value)


class CessacaoReadSerializer(serializers.ModelSerializer):
    """Serializador de leitura para cessação.

    Retorna dados de cessação e eventual insubsistência para exibição de ato.
    """

    # Campos do ato pai (designação)
    ato_pai_id = serializers.IntegerField(read_only=True)

    # Campos de CessacaoDetalhe
    a_pedido = serializers.BooleanField(
        source="cessacao_detalhe.a_pedido", read_only=True
    )
    remocao = serializers.BooleanField(
        source="cessacao_detalhe.remocao", read_only=True
    )
    aposentadoria = serializers.BooleanField(
        source="cessacao_detalhe.aposentadoria", read_only=True
    )
    data_cessacao = serializers.DateField(
        source="cessacao_detalhe.data_cessacao", read_only=True
    )

    insubsistencia = serializers.SerializerMethodField()
    apostilas = serializers.SerializerMethodField()

    class Meta:
        model = AtoAdministrativo
        fields = [
            "id",
            "tipo",
            "status",
            "ato_pai_id",
            "ato_raiz_id",
            "numero_portaria",
            "ano_vigente",
            "sei_numero",
            "doc",
            "criado_em",
            "a_pedido",
            "remocao",
            "aposentadoria",
            "data_cessacao",
            "insubsistencia",
            "apostilas",
        ]

    def get_insubsistencia(self, obj: AtoAdministrativo) -> dict | None:
        """Retorna a insubsistência associada à cessação.

        Args:
            obj: Instância de AtoAdministrativo.

        Returns:
            dict|None: Dados da insubsistência ou None se não houver.

        """
        for filho in obj.filhos.all():
            if filho.tipo == AtoAdministrativo.Tipo.INSUBSISTENCIA:
                detalhe = getattr(filho, "insubsistencia_detalhe", None)
                return {
                    "id": filho.id,
                    "observacoes": detalhe.observacoes if detalhe else "",
                }
        return None

    def get_apostilas(self, obj: AtoAdministrativo) -> list:
        """Retorna as apostilas ativas vinculadas à cessação.

        Args:
            obj: Instância de AtoAdministrativo.

        Returns:
            list: Apostilas serializadas, excluindo as insubsistentes.

        """
        resultado = []
        for filho in obj.filhos.all():
            if (
                filho.tipo != AtoAdministrativo.Tipo.APOSTILA
                or filho.status == "insubsistente"
            ):
                continue
            detalhe = getattr(filho, "apostila_detalhe", None)
            resultado.append(
                {
                    "id": filho.id,
                    "sei_numero": filho.sei_numero,
                    "doc": filho.doc,
                    "status": filho.status,
                    "observacao": detalhe.observacao if detalhe else "",
                    "criado_em": filho.criado_em,
                }
            )
        return resultado


class CessacaoReadSerializerById(AtoRelacionadoMixin, CessacaoReadSerializer):
    """Serializador de leitura para cessação v2.

    Retorna dados de cessação, insubsistência e designação para
    exibição dos detalhes de ato.
    """

    designacao = serializers.SerializerMethodField()

    class Meta:
        model = AtoAdministrativo
        fields = [
            "id",
            "tipo",
            "status",
            "ato_pai_id",
            "ato_raiz_id",
            "numero_portaria",
            "ano_vigente",
            "sei_numero",
            "doc",
            "criado_em",
            "a_pedido",
            "remocao",
            "aposentadoria",
            "data_cessacao",
            "insubsistencia",
            "apostilas",
            "designacao",
        ]
