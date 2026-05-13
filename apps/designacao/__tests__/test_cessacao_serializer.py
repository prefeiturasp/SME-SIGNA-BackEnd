import pytest
from apps.designacao.api.serializers.v2.cessacao_serializer import (
    CessacaoV2WriteSerializer,
    CessacaoV2ReadSerializer,
)
from apps.designacao.__tests__.factories import (
    criar_ato_designacao,
    criar_ato_cessacao,
    criar_ato_insubsistencia,
)


@pytest.mark.django_db
class TestCessacaoV2WriteSerializer:

    def _payload(self, ato_pai_id):
        return {
            'ato_pai': ato_pai_id,
            'numero_portaria': '12345',
            'ano_vigente': '2024',
            'sei_numero': '999999',
            'a_pedido': True,
            'data_cessacao': '2024-03-10',
        }

    def test_serializer_valido(self):
        d = criar_ato_designacao()
        s = CessacaoV2WriteSerializer(data=self._payload(d.id))
        assert s.is_valid(), s.errors

    def test_numero_portaria_invalido(self):
        d = criar_ato_designacao()
        payload = self._payload(d.id)
        payload['numero_portaria'] = '12A45'
        s = CessacaoV2WriteSerializer(data=payload)
        assert not s.is_valid()
        assert 'numero_portaria' in s.errors

    def test_ano_vigente_invalido(self):
        d = criar_ato_designacao()
        payload = self._payload(d.id)
        payload['ano_vigente'] = '20A4'
        s = CessacaoV2WriteSerializer(data=payload)
        assert not s.is_valid()
        assert 'ano_vigente' in s.errors

    def test_ato_pai_invalido_rejeita(self):
        payload = self._payload(9999)
        s = CessacaoV2WriteSerializer(data=payload)
        assert not s.is_valid()
        assert 'ato_pai' in s.errors


@pytest.mark.django_db
class TestCessacaoV2ReadSerializer:

    def test_get_insubsistencia_retorna_dados_quando_existe(self):
        d = criar_ato_designacao()
        c = criar_ato_cessacao(d)
        insub = criar_ato_insubsistencia(c)

        # Simula o prefetch que a view faz
        from apps.designacao.models.ato_administrativo import AtoAdministrativo
        c_com_prefetch = (
            AtoAdministrativo.objects
            .filter(pk=c.pk)
            .prefetch_related('filhos', 'filhos__insubsistencia_detalhe')
            .first()
        )
        data = CessacaoV2ReadSerializer(c_com_prefetch).data

        assert data['insubsistencia'] is not None
        assert data['insubsistencia']['id'] == insub.id

    def test_get_insubsistencia_retorna_none_quando_nao_existe(self):
        d = criar_ato_designacao()
        c = criar_ato_cessacao(d)

        from apps.designacao.models.ato_administrativo import AtoAdministrativo
        c_com_prefetch = (
            AtoAdministrativo.objects
            .filter(pk=c.pk)
            .prefetch_related('filhos', 'filhos__insubsistencia_detalhe')
            .first()
        )
        data = CessacaoV2ReadSerializer(c_com_prefetch).data

        assert data['insubsistencia'] is None
