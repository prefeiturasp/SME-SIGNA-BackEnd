"""Serializador para listagem de atos administrativos.

Fornece campos e representações customizadas para exibir
atos administrativos na tela de
listagem de atos administrativos.
"""

from rest_framework import serializers

from apps.designacao.api.serializers.portaria_serializer import (
    PortariaListSerializer,
)
from apps.designacao.models.ato_administrativo import AtoAdministrativo


class AtoAdministrativoListSerializer(PortariaListSerializer):
    """Serializador de ato administrativo para listagem.

    Representa atos administrativos com informações de ato,
    tipo de ato, portaria, datas,
    observações, nome e numero sei.
    """

    # Filhos (preenchidos com prefetch_related na view)
    cessacao = serializers.SerializerMethodField()
    apostilas = serializers.SerializerMethodField()
    insubsistencia = serializers.SerializerMethodField()
    criado_por_nome = serializers.SerializerMethodField()
    rf = serializers.SerializerMethodField()

    class Meta:
        model = AtoAdministrativo
        fields = [
            "id",
            "tipo_de_ato",
            "criado_em",
            "criado_por_nome",
            "observacoes",
            "numero_portaria",
            "ano_vigente",
            "nome",
            "rf",
            "status_publicacao",
            "sei_numero",
            "tipo",
            "cessacao",
            "apostilas",
            "insubsistencia",
            "tipo_insubsistencia",
            "ato_pai_id",
        ]

    def get_criado_por_nome(self, obj: AtoAdministrativo) -> str | None:
        """Retorna o nome do responsável pela criação do ato.

        Args:
            obj: Instância de AtoAdministrativo.

        Returns:
            str|None: Nome ou username do responsável, ou None se não
            houver.

        """
        responsavel = obj.criado_por
        if not responsavel:
            return None
        return responsavel.name or responsavel.username

    def get_rf(self, obj: AtoAdministrativo) -> str | None:
        """Retorna o RF do servidor indicado relacionado ao ato.

        Args:
            obj: Instância de AtoAdministrativo.

        Returns:
            str|None: RF do indicado ou None se não houver detalhe de
            designação relacionado.

        """
        detalhe = self._get_designacao_detalhe(obj)
        if detalhe:
            return detalhe.indicado_rf
        return None

    def get_cessacao(self, obj: AtoAdministrativo) -> dict | None:
        """Retorna dados da cessação associada à designação.

        Args:
            obj: Instância de AtoAdministrativo.

        Returns:
            dict|None: Dados simplificados da cessação ou None se não existir.

        """
        # Usa filhos prefetchados (.all() aproveita o cache do prefetch_related)  # noqa: E501
        cessacao_ato = next(
            (
                f
                for f in obj.filhos.all()
                if f.tipo == AtoAdministrativo.Tipo.CESSACAO
            ),
            None,
        )
        if not cessacao_ato:
            return None
        try:
            return {
                "id": cessacao_ato.id,
                "sei_numero": cessacao_ato.sei_numero,
                "doc": cessacao_ato.doc,
            }
        except Exception:
            return None

    def _serializar_apostilas(self, ato: AtoAdministrativo) -> list:
        """Serializa apostilas relacionadas a um ato.

        Args:
            ato: Instância de AtoAdministrativo.

        Returns:
            list: Lista de apostilas serializadas.

        """
        resultado = []
        for f in ato.filhos.all():
            if f.tipo != AtoAdministrativo.Tipo.APOSTILA:
                continue
            try:
                resultado.append(
                    {
                        "id": f.id,
                        "sei_numero": f.sei_numero,
                        "doc": f.doc,
                    }
                )
            except Exception:
                print(f"Erro ao serializar apostila: {f.id}")
        return resultado

    def get_apostilas(self, obj: AtoAdministrativo) -> list:
        """Retorna as apostilas associadas ao ato.

        Args:
            obj: Instância de AtoAdministrativo.

        Returns:
            list: Lista de apostilas serializadas.

        """
        return self._serializar_apostilas(obj)

    def _serializar_insubsistencia(
        self, ato: AtoAdministrativo
    ) -> dict | None:
        """Serializa a insubsistência válida de um ato.

        Args:
            ato: Instância de AtoAdministrativo representando o ato pai.

        Returns:
            dict|None: Dados de insubsistência ou None se não houver ato
            válido.

        """
        insub = next(
            (
                f
                for f in ato.filhos.all()
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
                "observacoes": d.observacoes,
            }
        except Exception:
            return None

    def get_insubsistencia(self, obj: AtoAdministrativo) -> dict | None:
        """Retorna a insubsistência ativa da designação.

        Args:
            obj: Instância de AtoAdministrativo.

        Returns:
            dict|None: Dados da insubsistência ou None se não existir.

        """
        # Retorna a insubsistência que ainda está ativa (não foi tornada sem efeito)  # noqa: E501
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
            return {
                "id": insub.id,
                "sei_numero": insub.sei_numero,
                "doc": insub.doc,
            }
        except Exception:
            return None
