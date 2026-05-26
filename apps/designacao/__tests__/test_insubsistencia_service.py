import pytest
from rest_framework.exceptions import ValidationError

from apps.designacao.services.insubsistencia_service import InsubsistenciaService
from apps.designacao.__tests__.factories import (
    criar_ato_designacao,
    criar_ato_cessacao,
    criar_ato_insubsistencia,
)


def _data(ato_pai, **kwargs):
    base = {
        "ato_pai": ato_pai,
        "numero_portaria": "111",
        "ano_vigente": "2024",
        "sei_numero": "SEI-I",
        "observacoes": "",
    }
    base.update(kwargs)
    return base


@pytest.mark.django_db
class TestInsubsistenciaService:

    def test_criar_insubsistencia_de_designacao(self):
        d = criar_ato_designacao()
        ato = InsubsistenciaService.criar(_data(d))
        assert ato.pk is not None
        assert ato.ato_pai_id == d.pk

    def test_criar_insubsistencia_de_cessacao(self):
        d = criar_ato_designacao()
        c = criar_ato_cessacao(d)
        ato = InsubsistenciaService.criar(_data(c))
        assert ato.pk is not None

    def test_erro_ato_ja_insubsistente(self):
        d = criar_ato_designacao()
        InsubsistenciaService.criar(_data(d))
        d.refresh_from_db()
        with pytest.raises(ValidationError, match="insubsistente"):
            InsubsistenciaService.criar(_data(d))

    def test_erro_insubsistencia_duplicada(self):
        d = criar_ato_designacao()
        criar_ato_insubsistencia(d)
        with pytest.raises(ValidationError):
            InsubsistenciaService.criar(_data(d))

    def test_tornar_sem_efeito_insubsistencia(self):
        d = criar_ato_designacao()
        insub = InsubsistenciaService.criar(_data(d))
        d.refresh_from_db()
        assert not d.eh_valido

        InsubsistenciaService.criar(_data(insub, sei_numero="SEI-TSE"))
        d.refresh_from_db()
        assert d.eh_valido

    def test_insubsistencia_de_apostila_reverte_campos(self):
        d = criar_ato_designacao(numero_portaria="001")
        from apps.designacao.services.apostila_service import ApostilaService

        ApostilaService.criar(
            {
                "ato_pai": d,
                "sei_numero": "SEI-A",
                "observacao": "X",
                "alteracoes": [
                    {"campo_alterado": "numero_portaria", "valor_novo": "999"}
                ],
            }
        )
        d.refresh_from_db()
        assert d.numero_portaria == "999"

        ap = d.filhos.filter(tipo="APOSTILA").first()
        InsubsistenciaService.criar(_data(ap))

        d.refresh_from_db()
        assert d.numero_portaria == "001"

    def test_insubsistencia_de_designacao_reverte_apostilas_filhas(self):
        d = criar_ato_designacao(numero_portaria="001")
        from apps.designacao.services.apostila_service import ApostilaService

        ApostilaService.criar(
            {
                "ato_pai": d,
                "sei_numero": "SEI-A",
                "observacao": "X",
                "alteracoes": [
                    {"campo_alterado": "numero_portaria", "valor_novo": "999"}
                ],
            }
        )
        d.refresh_from_db()
        assert d.numero_portaria == "999"

        InsubsistenciaService.criar(_data(d))

        d.refresh_from_db()
        assert d.numero_portaria == "001"

    def test_insubsistencia_de_designacao_anula_apostilas_ativas(self):
        from apps.designacao.services.apostila_service import ApostilaService
        from apps.designacao.models.ato_administrativo import AtoAdministrativo

        d = criar_ato_designacao()
        ApostilaService.criar(
            {
                "ato_pai": d,
                "sei_numero": "SEI-A",
                "observacao": "X",
                "alteracoes": [],
            }
        )
        apostila = d.filhos.filter(tipo=AtoAdministrativo.Tipo.APOSTILA).first()
        assert apostila.ativo

        InsubsistenciaService.criar(_data(d))

        apostila.refresh_from_db()
        assert not apostila.ativo

    def test_insubsistencia_de_cessacao_anula_apostilas_da_cessacao(self):
        from apps.designacao.services.apostila_service import ApostilaService
        from apps.designacao.models.ato_administrativo import AtoAdministrativo

        d = criar_ato_designacao()
        c = criar_ato_cessacao(d)
        ApostilaService.criar(
            {
                "ato_pai": c,
                "sei_numero": "SEI-A",
                "observacao": "X",
                "alteracoes": [],
            }
        )
        apostila = c.filhos.filter(tipo=AtoAdministrativo.Tipo.APOSTILA).first()
        assert apostila.ativo

        InsubsistenciaService.criar(_data(c))

        apostila.refresh_from_db()
        assert not apostila.ativo

    def test_insubsistencia_reverte_booleano_de_designacao_detalhe(self):
        from apps.designacao.services.apostila_service import ApostilaService

        d = criar_ato_designacao()
        assert not d.designacao_detalhe.carater_excepcional

        ApostilaService.criar(
            {
                "ato_pai": d,
                "sei_numero": "SEI-B",
                "observacao": "X",
                "alteracoes": [
                    {"campo_alterado": "carater_excepcional", "valor_novo": "True"}
                ],
            }
        )
        d.designacao_detalhe.refresh_from_db()
        assert d.designacao_detalhe.carater_excepcional

        InsubsistenciaService.criar(_data(d))

        d.designacao_detalhe.refresh_from_db()
        assert not d.designacao_detalhe.carater_excepcional

    def test_insubsistencia_reverte_booleano_de_cessacao_detalhe(self):
        from apps.designacao.services.apostila_service import ApostilaService

        d = criar_ato_designacao()
        c = criar_ato_cessacao(d)
        assert not c.cessacao_detalhe.a_pedido

        ApostilaService.criar(
            {
                "ato_pai": c,
                "sei_numero": "SEI-C",
                "observacao": "X",
                "alteracoes": [{"campo_alterado": "a_pedido", "valor_novo": "True"}],
            }
        )
        c.cessacao_detalhe.refresh_from_db()
        assert c.cessacao_detalhe.a_pedido

        InsubsistenciaService.criar(_data(c))

        c.cessacao_detalhe.refresh_from_db()
        assert not c.cessacao_detalhe.a_pedido
