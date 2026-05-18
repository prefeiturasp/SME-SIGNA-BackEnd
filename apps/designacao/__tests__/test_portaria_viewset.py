import pytest
import secrets
from datetime import date

from django.contrib.auth import get_user_model
from rest_framework.test import APIClient

from apps.designacao.models.ato_administrativo import AtoAdministrativo
from apps.designacao.models.designacao_detalhe import DesignacaoDetalhe
from apps.designacao.models.cessacao_detalhe import CessacaoDetalhe
from apps.designacao.models.insubsistencia_detalhe import InsubsistenciaDetalhe
from apps.designacao.models.apostila_detalhe import ApostilaDetalhe

User = get_user_model()


# ─── URLs ─────────────────────────────────────────────────────────────────────

URL_LIST = '/api/designacao/portarias/'
URL_ATUALIZAR = '/api/designacao/portarias/atualizar-data-publicacao/'


# ─── Fixtures ─────────────────────────────────────────────────────────────────

@pytest.fixture
def auth_client(db):
    password = secrets.token_urlsafe(16)
    user = User.objects.create_user(username='test_portaria', password=password)
    client = APIClient()
    client.force_authenticate(user=user)
    return client


@pytest.fixture
def designacao(db):
    ato = AtoAdministrativo.objects.create(
        tipo='DESIGNACAO',
        numero_portaria='001/2024',
        ano_vigente='2024',
        sei_numero='6018.2024/0001234-5',
        doc='',
        ativo=True,
    )
    DesignacaoDetalhe.objects.create(
        ato=ato,
        dre_nome='DRE BUTANTA',
        unidade_proponente='EMEF TESTE 1',
        codigo_hierarquico='108600',
        indicado_nome_servidor='MARIA SILVA',
        indicado_nome_civil='Maria da Silva',
        indicado_rf='12345678',
        indicado_vinculo=1,
        indicado_cargo_base='PROFESSOR DE EF I',
        indicado_lotacao='EMEF TESTE 1',
        indicado_cargo_sobreposto='DIRETOR DE ESCOLA',
        indicado_codigo_cargo_sobreposto=3360,
        indicado_local_exercicio='EMEF TESTE 1',
        data_inicio=date(2024, 1, 15),
        tipo_vaga='VAGO',
        cargo_vaga=3360,
    )
    return ato


@pytest.fixture
def designacao_2(db):
    ato = AtoAdministrativo.objects.create(
        tipo='DESIGNACAO',
        numero_portaria='002/2024',
        ano_vigente='2024',
        sei_numero='6018.2024/0002345-6',
        doc='',
        ativo=True,
    )
    DesignacaoDetalhe.objects.create(
        ato=ato,
        dre_nome='DRE IPIRANGA',
        unidade_proponente='EMEF TESTE 2',
        codigo_hierarquico='108700',
        indicado_nome_servidor='JOAO SOUZA',
        indicado_nome_civil='Joao de Souza',
        indicado_rf='87654321',
        indicado_vinculo=1,
        indicado_cargo_base='PROFESSOR DE EF II',
        indicado_lotacao='EMEF TESTE 2',
        indicado_cargo_sobreposto='COORDENADOR PEDAGOGICO',
        indicado_codigo_cargo_sobreposto=3379,
        indicado_local_exercicio='EMEF TESTE 2',
        data_inicio=date(2024, 2, 1),
        tipo_vaga='DISPONIVEL',
        cargo_vaga=3379,
    )
    return ato


@pytest.fixture
def cessacao(db, designacao):
    ato = AtoAdministrativo.objects.create(
        tipo='CESSACAO',
        numero_portaria='003/2024',
        ano_vigente='2024',
        sei_numero='6018.2024/0003456-7',
        doc='',
        ativo=True,
        ato_pai=designacao,
    )
    CessacaoDetalhe.objects.create(
        ato=ato,
        data_cessacao=date(2024, 6, 30),
    )
    return ato


@pytest.fixture
def insubsistencia(db, designacao):
    ato = AtoAdministrativo.objects.create(
        tipo='INSUBSISTENCIA',
        numero_portaria='004/2024',
        ano_vigente='2024',
        sei_numero='6018.2024/0004567-8',
        doc='',
        ativo=True,
        ato_pai=designacao,
    )
    InsubsistenciaDetalhe.objects.create(
        ato=ato,
        observacoes='Revogada por erro.',
    )
    return ato


@pytest.fixture
def apostila(db, designacao):
    ato = AtoAdministrativo.objects.create(
        tipo='APOSTILA',
        numero_portaria='005/2024',
        ano_vigente='2024',
        sei_numero='6018.2024/0005678-9',
        doc='',
        ativo=True,
        ato_pai=designacao,
    )
    ApostilaDetalhe.objects.create(
        ato=ato,
        observacao='Retificacao de cargo.',
    )
    return ato


@pytest.fixture
def inativo(db):
    return AtoAdministrativo.objects.create(
        tipo='DESIGNACAO',
        numero_portaria='099/2024',
        ano_vigente='2024',
        sei_numero='6018.2024/0099999-9',
        doc='',
        ativo=False,
    )


# ─── Testes: GET /portarias/ ──────────────────────────────────────────────────

@pytest.mark.django_db
class TestPortariaListView:

    def test_retorna_200(self, auth_client, designacao):
        response = auth_client.get(URL_LIST)
        assert response.status_code == 200

    def test_retorna_lista(self, auth_client, designacao, designacao_2):
        response = auth_client.get(URL_LIST)
        assert isinstance(response.data, list)
        assert len(response.data) == 2

    def test_campos_retornados(self, auth_client, designacao):
        response = auth_client.get(URL_LIST)
        item = response.data[0]
        assert set(item.keys()) == {
            'id', 'portaria', 'doc', 'tipo_de_ato',
            'nome', 'cargo', 'data_designacao',
            'data_cessacao', 'numero_sei', 'observacoes',
        }

    def test_ordenacao_padrao_por_numero_portaria(self, auth_client, designacao, designacao_2):
        response = auth_client.get(URL_LIST)
        portarias = [item['portaria'] for item in response.data]
        assert portarias == sorted(portarias)

    def test_sem_paginacao(self, auth_client, designacao, designacao_2):
        response = auth_client.get(URL_LIST)
        # Sem paginação: retorna lista direta, não dict com 'results'
        assert isinstance(response.data, list)

    # ── Filtros ───────────────────────────────────────────────────────────────

    def test_filtro_tipo_designacao(self, auth_client, designacao, cessacao):
        response = auth_client.get(URL_LIST, {'tipo': 'DESIGNACAO'})
        assert response.status_code == 200
        assert all(item['tipo_de_ato'] == 'Designação' for item in response.data)

    def test_filtro_tipo_cessacao(self, auth_client, designacao, cessacao):
        response = auth_client.get(URL_LIST, {'tipo': 'CESSACAO'})
        assert response.status_code == 200
        assert all(item['tipo_de_ato'] == 'Cessação' for item in response.data)

    def test_filtro_tipo_designacao_cessacao(self, auth_client, designacao, cessacao, insubsistencia):
        response = auth_client.get(URL_LIST, {'tipo': 'DESIGNACAO_CESSACAO'})
        assert response.status_code == 200
        tipos = {item['tipo_de_ato'] for item in response.data}
        assert tipos.issubset({'Designação', 'Cessação'})
        assert 'Insubsistência' not in tipos

    def test_filtro_ano(self, auth_client, designacao, designacao_2):
        response = auth_client.get(URL_LIST, {'ano': '2024'})
        assert response.status_code == 200
        assert len(response.data) == 2

    def test_filtro_ano_sem_resultado(self, auth_client, designacao):
        response = auth_client.get(URL_LIST, {'ano': '1900'})
        assert response.status_code == 200
        assert len(response.data) == 0

    def test_filtro_numero_sei(self, auth_client, designacao, designacao_2):
        response = auth_client.get(URL_LIST, {'numero_sei': '0001234'})
        assert response.status_code == 200
        assert len(response.data) == 1
        assert response.data[0]['numero_sei'] == '6018.2024/0001234-5'

    def test_filtro_portaria_inicial(self, auth_client, designacao, designacao_2):
        response = auth_client.get(URL_LIST, {'portaria_inicial': '002/2024'})
        assert response.status_code == 200
        portarias = [item['portaria'] for item in response.data]
        assert all(p >= '002/2024' for p in portarias)

    def test_filtro_portaria_final(self, auth_client, designacao, designacao_2):
        response = auth_client.get(URL_LIST, {'portaria_final': '001/2024'})
        assert response.status_code == 200
        portarias = [item['portaria'] for item in response.data]
        assert all(p <= '001/2024' for p in portarias)

    def test_filtro_nome(self, auth_client, designacao, designacao_2):
        response = auth_client.get(URL_LIST, {'nome': 'MARIA'})
        assert response.status_code == 200
        assert len(response.data) == 1
        assert response.data[0]['nome'] == 'MARIA SILVA'

    def test_filtro_rf(self, auth_client, designacao, designacao_2):
        response = auth_client.get(URL_LIST, {'rf': '12345678'})
        assert response.status_code == 200
        assert len(response.data) == 1

    def test_filtro_dre(self, auth_client, designacao, designacao_2):
        response = auth_client.get(URL_LIST, {'dre': 'BUTANTA'})
        assert response.status_code == 200
        assert len(response.data) == 1

    def test_filtro_data_cessacao(self, auth_client, designacao, cessacao):
        response = auth_client.get(URL_LIST, {'data_cessacao': '2024-06-30'})
        assert response.status_code == 200
        assert len(response.data) == 1
        assert response.data[0]['id'] == cessacao.pk

    # ── Search ────────────────────────────────────────────────────────────────

    def test_search_por_numero_portaria(self, auth_client, designacao, designacao_2):
        response = auth_client.get(URL_LIST, {'search': '001/2024'})
        assert response.status_code == 200
        assert len(response.data) == 1
        assert response.data[0]['portaria'] == '001/2024'

    def test_search_por_sei(self, auth_client, designacao, designacao_2):
        response = auth_client.get(URL_LIST, {'search': '0002345'})
        assert response.status_code == 200
        assert len(response.data) == 1

    def test_search_por_nome_servidor(self, auth_client, designacao, designacao_2):
        response = auth_client.get(URL_LIST, {'search': 'JOAO'})
        assert response.status_code == 200
        assert len(response.data) == 1
        assert response.data[0]['nome'] == 'JOAO SOUZA'

    # ── Ordering ──────────────────────────────────────────────────────────────

    def test_ordering_por_numero_portaria_asc(self, auth_client, designacao, designacao_2):
        response = auth_client.get(URL_LIST, {'ordering': 'numero_portaria'})
        portarias = [item['portaria'] for item in response.data]
        assert portarias == sorted(portarias)

    def test_ordering_por_numero_portaria_desc(self, auth_client, designacao, designacao_2):
        response = auth_client.get(URL_LIST, {'ordering': '-numero_portaria'})
        portarias = [item['portaria'] for item in response.data]
        assert portarias == sorted(portarias, reverse=True)

    # ── Todos os tipos retornados ─────────────────────────────────────────────

    def test_retorna_todos_os_tipos(self, auth_client, designacao, cessacao, insubsistencia, apostila):
        response = auth_client.get(URL_LIST)
        assert response.status_code == 200
        tipos = {item['tipo_de_ato'] for item in response.data}
        assert tipos == {'Designação', 'Cessação', 'Insubsistência', 'Apostila'}


# ─── Testes: POST /portarias/atualizar-data-publicacao/ ───────────────────────

@pytest.mark.django_db
class TestAtualizarDataPublicacao:

    def test_atualiza_doc_com_sucesso(self, auth_client, designacao, designacao_2):
        payload = {
            'ids': [designacao.pk, designacao_2.pk],
            'data_publicacao': '10.234',
        }
        response = auth_client.post(URL_ATUALIZAR, payload, format='json')
        assert response.status_code == 200
        assert response.data['detail'] == '2 ato(s) atualizado(s) com sucesso.'
        assert response.data['data_publicacao'] == '10.234'
        assert set(response.data['ids']) == {designacao.pk, designacao_2.pk}

    def test_doc_atualizado_no_banco(self, auth_client, designacao):
        auth_client.post(URL_ATUALIZAR, {'ids': [designacao.pk], 'data_publicacao': '99.999'}, format='json')
        designacao.refresh_from_db()
        assert designacao.doc == '99.999'

    def test_nao_atualiza_inativo(self, auth_client, inativo):
        payload = {'ids': [inativo.pk], 'data_publicacao': '10.234'}
        response = auth_client.post(URL_ATUALIZAR, payload, format='json')
        assert response.status_code == 400

    def test_erro_sem_ids(self, auth_client):
        response = auth_client.post(URL_ATUALIZAR, {'data_publicacao': '10.234'}, format='json')
        assert response.status_code == 400
        assert 'ids' in response.data

    def test_erro_ids_vazio(self, auth_client):
        response = auth_client.post(URL_ATUALIZAR, {'ids': [], 'data_publicacao': '10.234'}, format='json')
        assert response.status_code == 400
        assert 'ids' in response.data

    def test_erro_sem_data_publicacao(self, auth_client, designacao):
        response = auth_client.post(URL_ATUALIZAR, {'ids': [designacao.pk]}, format='json')
        assert response.status_code == 400
        assert 'data_publicacao' in response.data

    def test_erro_data_publicacao_vazia(self, auth_client, designacao):
        response = auth_client.post(URL_ATUALIZAR, {'ids': [designacao.pk], 'data_publicacao': ''}, format='json')
        assert response.status_code == 400
        assert 'data_publicacao' in response.data

    def test_erro_ids_inexistentes(self, auth_client):
        response = auth_client.post(URL_ATUALIZAR, {'ids': [99999], 'data_publicacao': '10.234'}, format='json')
        assert response.status_code == 400
        assert 'ids' in response.data

    def test_atualiza_apenas_ids_informados(self, auth_client, designacao, designacao_2):
        auth_client.post(URL_ATUALIZAR, {'ids': [designacao.pk], 'data_publicacao': 'NOVO'}, format='json')
        designacao.refresh_from_db()
        designacao_2.refresh_from_db()
        assert designacao.doc == 'NOVO'
        assert designacao_2.doc == ''  # não foi alterado