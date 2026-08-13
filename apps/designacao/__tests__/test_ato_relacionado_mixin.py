"""Testes para o mixin de atos relacionados (designação/cessação)."""

from unittest.mock import Mock

from apps.designacao.api.serializers.ato_relacionado_mixin import (
    AtoRelacionadoMixin,
)
from apps.designacao.models.ato_administrativo import AtoAdministrativo


class TestAtoRelacionadoMixin:
    """Testes para AtoRelacionadoMixin."""

    def test_get_designacao_ato_administrativo_retorna_none_sem_raiz(self):
        """Verifica que retorna None quando não há raiz nem pai."""
        mixin = AtoRelacionadoMixin()
        obj = Mock(
            tipo=AtoAdministrativo.Tipo.APOSTILA, ato_raiz=None, ato_pai=None
        )

        assert mixin._get_designacao_ato_administrativo(obj) is None

    def test_get_cessacao_ato_administrativo_retorna_via_raiz(self):
        """Verifica que retorna a raiz quando ela é do tipo cessação."""
        mixin = AtoRelacionadoMixin()
        raiz = Mock(tipo=AtoAdministrativo.Tipo.CESSACAO)
        pai = Mock(tipo=AtoAdministrativo.Tipo.DESIGNACAO)
        obj = Mock(
            tipo=AtoAdministrativo.Tipo.APOSTILA, ato_raiz=raiz, ato_pai=pai
        )

        assert mixin._get_cessacao_ato_administrativo(obj) is raiz

    def test_get_designacao_retorna_none_sem_designacao_na_cadeia(self):
        """Verifica que get_designacao retorna None sem designação na cadeia."""
        mixin = AtoRelacionadoMixin()
        obj = Mock(
            tipo=AtoAdministrativo.Tipo.APOSTILA, ato_raiz=None, ato_pai=None
        )

        assert mixin.get_designacao(obj) is None
