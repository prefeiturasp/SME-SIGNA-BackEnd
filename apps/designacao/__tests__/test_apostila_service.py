import pytest
from rest_framework.exceptions import ValidationError
from apps.designacao.models.apostila import Apostila
from apps.designacao.services.apostila_service import ApostilaService
from apps.designacao.models.designacao import Designacao
from apps.designacao.models.cessacao import Cessacao
from django.utils import timezone

@pytest.mark.django_db
class TestApostilaService:

    @pytest.fixture
    def designacao(self):
        return Designacao.objects.create(
            dre_nome="DRE ITAQUERA",
            unidade_proponente="EMEF TESTE",
            codigo_hierarquico="123",
            indicado_nome_civil="JOSE",
            indicado_nome_servidor="JOSE",
            indicado_rf="1234567",
            indicado_vinculo=1,
            indicado_cargo_base="PROFESSOR",
            indicado_lotacao="ESCOLA A",
            indicado_local_exercicio="ESCOLA A",
            numero_portaria="123",
            ano_vigente="2026",
            sei_numero="111",
            data_inicio=timezone.now().date(),
            tipo_vaga=Designacao.TipoVaga.DISPONIVEL,
            is_deleted=False
        )

    @pytest.fixture
    def cessacao(self, designacao):
        return Cessacao.objects.create(
            designacao=designacao,
            numero_portaria="456",
            ano_vigente="2026",
            sei_numero="222",
            data_designacao=timezone.now().date(),
            is_deleted=False
        )

    def test_criar_apostila_designacao_sucesso(self, designacao):
        data = {
            "designacao": designacao.id,
            "ato_apostilado": "designacao",
            "tipo": Apostila.Tipo.APOSTILA,
            "sei_numero": "12345",
            "observacao": "Teste",
            "d_o": "2026-01-01"
        }
        apostila = ApostilaService.criar_apostila(data)
        assert apostila.id is not None
        assert apostila.designacao == designacao
        assert apostila.cessacao is None

    def test_criar_apostila_cessacao_sucesso(self, designacao, cessacao):
        data = {
            "designacao": designacao.id,
            "ato_apostilado": "cessacao",
            "tipo": Apostila.Tipo.APOSTILA,
            "sei_numero": "54321",
            "observacao": "Teste",
        }
        apostila = ApostilaService.criar_apostila(data)
        assert apostila.id is not None
        assert apostila.cessacao == cessacao
        assert apostila.designacao is None

    def test_erro_tipo_ato_invalido(self, designacao):
        data = {
            "designacao": designacao.id,
            "ato_apostilado": "invalido",
            "tipo": Apostila.Tipo.APOSTILA
        }
        with pytest.raises(ValidationError):
            ApostilaService.criar_apostila(data)

    def test_erro_designacao_nao_encontrada(self):
        data = {"designacao": 9999, "ato_apostilado": "designacao"}
        with pytest.raises(ValidationError) as excinfo:
            ApostilaService.criar_apostila(data)
        assert "Designação não encontrada" in str(excinfo.value)

    def test_erro_ja_existe_apostila_ativa(self, designacao):
        Apostila.objects.create(
            tipo=Apostila.Tipo.APOSTILA,
            designacao=designacao,
            sei_numero="1",
            observacao="Obs"
        )
        data = {
            "designacao": designacao.id,
            "ato_apostilado": "designacao",
            "tipo": Apostila.Tipo.APOSTILA,
            "sei_numero": "2"
        }
        with pytest.raises(ValidationError):
            ApostilaService.criar_apostila(data)

    def test_permite_apos_anulacao(self, designacao):
        ap = Apostila.objects.create(tipo=Apostila.Tipo.APOSTILA, designacao=designacao, sei_numero="1", observacao="X")
        Apostila.objects.create(tipo=Apostila.Tipo.ANULACAO, designacao=designacao, apostila_referencia=ap, sei_numero="2", observacao="Y")
        
        data = {
            "designacao": designacao.id,
            "ato_apostilado": "designacao",
            "tipo": Apostila.Tipo.APOSTILA,
            "sei_numero": "3",
            "observacao": "Nova"
        }
        assert ApostilaService.criar_apostila(data).id is not None

    def test_erro_cessacao_inexistente_ou_deletada(self, designacao):
        data = {
            "designacao": designacao.id, 
            "ato_apostilado": "cessacao",
            "tipo": Apostila.Tipo.APOSTILA
        }
        with pytest.raises(ValidationError, match="Não existe cessação válida"):
            ApostilaService.criar_apostila(data)