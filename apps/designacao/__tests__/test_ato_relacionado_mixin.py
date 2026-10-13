"""Testes para o mixin de atos relacionados (designação/cessação)."""

from unittest.mock import Mock

import pytest

from apps.designacao.__tests__.factories import (
    criar_ato_apostila,
    criar_ato_cessacao,
    criar_ato_designacao,
)
from apps.designacao.api.serializers.apostila_serializer import (
    ApostilaReadSerializer,
)
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

    @pytest.mark.django_db
    def test_get_designacao_retorna_dados_da_designacao(self):
        """Verifica get_designacao com ato do tipo designação."""
        designacao = criar_ato_designacao()
        mixin = AtoRelacionadoMixin()

        dados = mixin.get_designacao(designacao)

        assert dados is not None
        assert dados["numero_portaria"] == designacao.numero_portaria
        assert dados["indicado_nome_servidor"] == "Nome Servidor"

    @pytest.mark.django_db
    def test_get_cessacao_retorna_dados_da_cessacao(self):
        """Verifica get_cessacao com ato do tipo cessação."""
        designacao = criar_ato_designacao()
        cessacao = criar_ato_cessacao(designacao, numero_portaria=50)
        mixin = AtoRelacionadoMixin()

        dados = mixin.get_cessacao(cessacao)

        assert dados is not None
        assert dados["numero_portaria"] == 50
        assert dados["a_pedido"] is False

    @pytest.mark.django_db
    def test_get_cessacao_detalhe_via_ato_pai(self):
        """Verifica _get_cessacao_detalhe quando o pai é cessação."""
        designacao = criar_ato_designacao()
        cessacao = criar_ato_cessacao(designacao)
        apostila = criar_ato_apostila(cessacao)
        mixin = AtoRelacionadoMixin()

        detalhe = mixin._get_cessacao_detalhe(apostila)

        assert detalhe is not None
        assert detalhe.ato_id == cessacao.id

    @pytest.mark.django_db
    def test_get_cessacao_ato_administrativo_via_ato_pai(self):
        """Verifica _get_cessacao_ato_administrativo via ato_pai."""
        designacao = criar_ato_designacao()
        cessacao = criar_ato_cessacao(designacao)
        apostila = criar_ato_apostila(cessacao)
        mixin = AtoRelacionadoMixin()

        ato_cessacao = mixin._get_cessacao_ato_administrativo(apostila)

        assert ato_cessacao is not None
        assert ato_cessacao.pk == cessacao.pk

    @pytest.mark.django_db
    def test_get_designacao_ato_administrativo_via_apostila(self):
        """Verifica _get_designacao_ato_administrativo via ato_pai."""
        designacao = criar_ato_designacao()
        apostila = criar_ato_apostila(designacao)
        mixin = AtoRelacionadoMixin()

        ato_designacao = mixin._get_designacao_ato_administrativo(apostila)

        assert ato_designacao is not None
        assert ato_designacao.pk == designacao.pk

    @pytest.mark.django_db
    def test_get_cessacao_retorna_none_para_apostila_de_designacao(self):
        """Verifica get_cessacao retorna None quando não há cessação."""
        designacao = criar_ato_designacao()
        apostila = criar_ato_apostila(designacao)
        mixin = AtoRelacionadoMixin()

        assert mixin.get_cessacao(apostila) is None

    @pytest.mark.django_db
    def test_mixin_integrado_no_read_serializer(self):
        """Verifica integração do mixin no serializer de leitura."""
        designacao = criar_ato_designacao()
        cessacao = criar_ato_cessacao(designacao, numero_portaria=50)
        apostila = criar_ato_apostila(cessacao)

        data = ApostilaReadSerializer(apostila).data

        assert (
            data["designacao"]["numero_portaria"] == designacao.numero_portaria
        )
        assert data["cessacao"]["numero_portaria"] == 50
