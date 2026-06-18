"""Serializador para listagem de atos administrativos.

Fornece campos e representações customizadas para exibir
atos administrativos na tela de
listagem de atos administrativos.
"""

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

    class Meta:
        model = AtoAdministrativo
        fields = [
            "id",
            "tipo_de_ato",
            "criado_em",
            "observacoes",
            "portaria",
            "ano_vigente",
            "nome",
            "status_publicacao",
            "numero_sei",
            "tipo",
        ]
