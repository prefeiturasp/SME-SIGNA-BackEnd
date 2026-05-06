import pytest
from unittest.mock import MagicMock

from apps.designacao.__tests__.factories import criar_designacao
from apps.designacao.models.cessacao import Cessacao
from apps.designacao.models.insubsistencia import Insubsistencia
from apps.designacao.services.insubsistencia_service import InsubsistenciaService


def _criar_cessacao(designacao, **kwargs):
    base = {
        "designacao": designacao,
        "numero_portaria": "12345",
        "ano_vigente": "2024",
        "sei_numero": "999999",
        "data_designacao": "2024-03-10",
    }
    base.update(kwargs)
    return Cessacao.objects.create(**base)


def _criar_insubsistencia(cessacao=None, designacao=None):
    return Insubsistencia.objects.create(
        cessacao=cessacao,
        designacao=designacao,
        numero_portaria="11111",
        ano_vigente="2024",
        sei_numero="888888",
    )


def _mock_serializer(validated_data):
    serializer = MagicMock()
    serializer.validated_data = validated_data
    return serializer


@pytest.mark.django_db
class TestMontarDadosInsubsistenciaCessacao:

    def test_seta_cessacao_e_limpa_designacao_quando_cessacao_existe(self):
        """
        Deve preencher cessacao e definir designacao como None
        quando a designacao possui uma cessacao vinculada.
        """
        designacao = criar_designacao()
        cessacao = _criar_cessacao(designacao)
        serializer = _mock_serializer({"designacao": designacao})

        resultado = InsubsistenciaService.montar_dados_insubsistencia_cessacao(serializer)

        assert resultado.validated_data["cessacao"] == cessacao
        assert resultado.validated_data["designacao"] is None


    def test_lanca_excecao_quando_designacao_nao_tem_cessacao(self):
        """
        Deve lançar Exception quando a designacao não possui cessacao vinculada.
        """
        designacao = criar_designacao()
        serializer = _mock_serializer({"designacao": designacao})

        with pytest.raises(Exception, match="Cessação não encontrada"):
            InsubsistenciaService.montar_dados_insubsistencia_cessacao(serializer)

    def test_lanca_excecao_quando_designacao_esta_deletada(self):
            designacao = criar_designacao()
            _criar_cessacao(designacao)
            
            designacao.delete() 

            serializer = _mock_serializer({"designacao": designacao})

            with pytest.raises(Exception):
                InsubsistenciaService.montar_dados_insubsistencia_cessacao(serializer)


@pytest.mark.django_db
class TestMontarDadosInsubsistenciaDesignacao:

    def test_nao_altera_serializer_quando_designacao_nao_tem_cessacao(self):
        """
        Deve retornar o serializer sem modificações quando a designacao
        não possui cessacao vinculada.
        """
        designacao = criar_designacao()
        serializer = _mock_serializer({"designacao": designacao})

        resultado = InsubsistenciaService.montar_dados_insubsistencia_designacao(serializer)

        assert "cessacao" not in resultado.validated_data

    def test_nao_altera_serializer_quando_cessacao_esta_deletada(self):
        """
        Deve retornar o serializer sem modificações quando a cessacao
        vinculada possui is_deleted=True.
        """
        designacao = criar_designacao()
        cessacao = _criar_cessacao(designacao)
        cessacao.delete()
        serializer = _mock_serializer({"designacao": designacao})

        resultado = InsubsistenciaService.montar_dados_insubsistencia_designacao(serializer)

        assert "cessacao" not in resultado.validated_data

    def test_seta_cessacao_quando_cessacao_ativa_e_sem_insubsistencia(self):
        designacao = criar_designacao()
        cessacao = _criar_cessacao(designacao)
        serializer = _mock_serializer({"designacao": designacao})

        resultado = InsubsistenciaService.montar_dados_insubsistencia_cessacao(serializer)

        assert resultado.validated_data["cessacao"] == cessacao
        assert resultado.validated_data["designacao"] is None

    def test_nao_seta_cessacao_quando_insubsistencia_ja_existe(self):
        """
        Deve NÃO preencher cessacao no validated_data quando já existe
        uma insubsistencia ativa vinculada à cessacao.
        """
        designacao = criar_designacao()
        cessacao = _criar_cessacao(designacao)
        _criar_insubsistencia(cessacao=cessacao)
        serializer = _mock_serializer({"designacao": designacao})

        resultado = InsubsistenciaService.montar_dados_insubsistencia_designacao(serializer)

        assert "cessacao" not in resultado.validated_data
        assert resultado.validated_data["designacao"] == designacao

    def test_lanca_excecao_quando_designacao_esta_deletada(self):
        designacao = criar_designacao()
        _criar_cessacao(designacao)
        
        designacao.delete() 
        
        serializer = _mock_serializer({"designacao": designacao})

        with pytest.raises(Exception):
            InsubsistenciaService.montar_dados_insubsistencia_cessacao(serializer)

    def test_designacao_sem_cessacao(self):
        """
        Deve retornar o mesmo objeto serializer recebido.
        """
        designacao = criar_designacao()
        serializer = _mock_serializer({"designacao": designacao})

        resultado = InsubsistenciaService.montar_dados_insubsistencia_designacao(serializer)

        assert resultado is serializer
