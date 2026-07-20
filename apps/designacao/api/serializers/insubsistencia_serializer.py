"""Serializadores para insubsistência.

Inclui definição de payloads para escrita e leitura de insubsistência em atos.
"""

from datetime import date

from rest_framework import serializers

from apps.designacao.api.serializers.ato_relacionado_mixin import (
    AtoRelacionadoMixin,
)
from apps.designacao.api.serializers.utils import (
    NullableDateField,
    validar_somente_numeros,
)
from apps.designacao.models.ato_administrativo import AtoAdministrativo


class InsubsistenciaWriteSerializer(serializers.Serializer):
    """Serializador de escrita para insubsistência.

    Valida os campos obrigatórios para criação de uma insubsistência.
    """

    ato_pai = serializers.PrimaryKeyRelatedField(
        queryset=AtoAdministrativo.objects.all()
    )
    numero_portaria = serializers.CharField(max_length=20)
    ano_vigente = serializers.CharField(max_length=6)
    sei_numero = serializers.CharField(max_length=30)
    doc = NullableDateField(required=False, default=None, allow_null=True)
    observacoes = serializers.CharField(
        allow_blank=True, required=False, default=""
    )
    texto_apostila = serializers.CharField(
        allow_blank=True, required=False, default=""
    )

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


class InsubsistenciaReadSerializer(
    AtoRelacionadoMixin, serializers.ModelSerializer
):
    """Serializador de leitura para insubsistência.

    Expõe status e observações da insubsistência.
    """

    status = serializers.SerializerMethodField()
    observacoes = serializers.CharField(
        source="insubsistencia_detalhe.observacoes", read_only=True
    )
    texto_apostila = serializers.SerializerMethodField()
    designacao = serializers.SerializerMethodField()
    cessacao = serializers.SerializerMethodField()
    insubsistencia = serializers.SerializerMethodField()
    tipo_insubsistencia = serializers.SerializerMethodField()
    ato_apostilado = serializers.SerializerMethodField()

    class Meta:
        model = AtoAdministrativo
        fields = [
            "id",
            "tipo",
            "status",
            "ato_pai_id",
            "numero_portaria",
            "ano_vigente",
            "sei_numero",
            "doc",
            "criado_em",
            "observacoes",
            "texto_apostila",
            "designacao",
            "cessacao",
            "insubsistencia",
            "tipo_insubsistencia",
            "ato_apostilado",
        ]

    def get_status(self, obj: AtoAdministrativo) -> str:
        """Retorna o status do ato de insubsistência.

        Args:
            obj: Instância de AtoAdministrativo.

        Returns:
            str: Status do ato.

        """
        return obj.status

    def get_texto_apostila(self, obj: AtoAdministrativo) -> str | None:
        """Retorna o texto da anulação quando a insubsistência é de apostila.

        Args:
            obj: Instância de AtoAdministrativo.

        Returns:
            str | None: Texto da anulação ou None se não aplicável.

        """
        detalhe = getattr(obj, "insubsistencia_apostila_detalhe", None)
        return detalhe.texto if detalhe else None

    def get_tipo_insubsistencia(self, obj: AtoAdministrativo) -> str | None:
        """Retorna o tipo de insubsistência.

        Args:
            obj: Instância de AtoAdministrativo.

        Returns:
            str | None: Tipo de insubsistência ou None se não aplicável.

        """
        if obj.ato_pai:
            return f"{obj.ato_pai.tipo}"
        return None

    def _get_ato_apostilado(
        self, obj: AtoAdministrativo
    ) -> AtoAdministrativo | None:
        """Retorna o ato administrativo de apostila relacionado."""
        pai = obj.ato_pai
        if pai:
            avo = pai.ato_pai
            if avo:
                return avo

        return None

    def get_ato_apostitextolado(self, obj: AtoAdministrativo) -> dict | None:
        """Retorna o  da anulação quando a insubsistência é de apostila.

        Args:
            obj: Instância de AtoAdministrativo.

        Returns:
            str | None: Texto da anulação ou None se não aplicável.

        """
        ato_apostilado = self._get_ato_apostilado(obj)

        detalhe = getattr(obj, "insubsistencia_apostila_detalhe", None)
        if ato_apostilado is not None:
            return {
                "numero_portaria": ato_apostilado.numero_portaria,
                "ano_vigente": ato_apostilado.ano_vigente,
                "sei_numero": ato_apostilado.sei_numero,
                "doc": ato_apostilado.doc,
                "texto": detalhe.texto if detalhe else None,
            }
        return None

    def _get_insubsistencia_ato_administrativo(
        self, obj: AtoAdministrativo
    ) -> AtoAdministrativo | None:
        """Retorna o ato administrativo de insubsistência relacionado."""
        pai = obj.ato_pai
        if pai and pai.tipo == AtoAdministrativo.Tipo.INSUBSISTENCIA:
            return pai

        return None

    def _get_doc_do_ato_insubsistido(
        self, obj: AtoAdministrativo | None
    ) -> date | None:
        """Retorna o doc do ato insubsistido."""
        if obj and obj.ato_pai:
            return obj.ato_pai.doc
        return None

    def get_insubsistencia(self, obj: AtoAdministrativo) -> dict | None:
        """Retorna os dados de insubsistência do ato ou do ato relacionado."""
        ato_insubsistencia = self._get_insubsistencia_ato_administrativo(obj)

        doc_do_ato_insubsistido = self._get_doc_do_ato_insubsistido(
            ato_insubsistencia
        )

        if ato_insubsistencia is not None:
            return {
                "numero_portaria": ato_insubsistencia.numero_portaria,
                "ano_vigente": ato_insubsistencia.ano_vigente,
                "sei_numero": ato_insubsistencia.sei_numero,
                "doc": ato_insubsistencia.doc,
                "doc_do_ato_insubsistido": doc_do_ato_insubsistido,
            }
        return None
