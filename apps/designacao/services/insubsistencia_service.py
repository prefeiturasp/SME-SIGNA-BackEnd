from ast import Dict
from typing import Any
from django.db.models import F
from apps.designacao.models.designacao import Designacao
from apps.designacao.models.insubsistencia import Insubsistencia
from apps.helpers.exceptions import CessacaoNotFoundError, InsubsistenciaNotFoundError


class InsubsistenciaService:

    @staticmethod
    def montar_dados_insubsistencia_cessacao(serializer):
        """
        Monta o dicionário padronizado de insubsistência de cessação.
        """

        designacao = serializer.validated_data.get('designacao')
 
 
        designacao_obj = Designacao.objects.select_related('cessacao').filter(
            id=designacao.id,
            is_deleted=False,
        ).first()


        cessacao_relacionada = getattr(designacao_obj, 'cessacao', None)
        if not cessacao_relacionada:
            raise CessacaoNotFoundError("Cessação não encontrada")

        serializer.validated_data['cessacao'] = cessacao_relacionada
        serializer.validated_data['designacao'] = None

        return serializer

    @staticmethod
    def montar_dados_insubsistencia_designacao(serializer):
        """
        Monta o dicionário padronizado de insubsistência de designação.
        """

        designacao = serializer.validated_data.get('designacao')
 
 
        designacao_obj = Designacao.objects.select_related('cessacao').filter(
            id=designacao.id,
            is_deleted=False,
        ).first()


        cessacao_relacionada = getattr(designacao_obj, 'cessacao', None)
        if cessacao_relacionada and not cessacao_relacionada.is_deleted:
            queryset_cessacao = Insubsistencia.objects.filter(
                cessacao_id=cessacao_relacionada.id,
                is_deleted=False,
            ) if cessacao_relacionada else Insubsistencia.objects.none()
            
            if not queryset_cessacao.exists():
                serializer.validated_data['cessacao'] = cessacao_relacionada

        
        return serializer