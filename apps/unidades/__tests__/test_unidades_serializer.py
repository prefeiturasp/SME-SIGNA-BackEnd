import pytest
from rest_framework.exceptions import ValidationError
from apps.unidades.api.serializers.unidades_serializer import DRESerializer, UnidadeSerializer


class TestDRESerializer:
    """Testes para o DRESerializer"""
    
    def test_serializer_com_dados_validos(self, dados_dre_validos):
        """Testa serialização com dados válidos"""
        serializer = DRESerializer(data=dados_dre_validos)
        assert serializer.is_valid(), serializer.errors
        assert serializer.validated_data['codigoDRE'] == '001'
        assert serializer.validated_data['nomeDRE'] == 'Diretoria Regional de Educação Centro'
        assert serializer.validated_data['siglaDRE'] == 'DRE-CT'
    
    def test_serializer_com_dados_faltando(self):
        """Testa serialização com campos obrigatórios faltando"""
        data = {'codigo_dre': '001'}
        
        serializer = DRESerializer(data=data)
        assert not serializer.is_valid()
        assert 'nome_dre' in serializer.errors
        assert 'sigla_dre' in serializer.errors
    
    def test_output_com_source_mapping(self):
        """Testa se o output usa os nomes padronizados"""
        instance = {
            'codigoDRE': '001',
            'nomeDRE': 'DRE Centro',
            'siglaDRE': 'DRE-CT'
        }
        
        serializer = DRESerializer(instance)
        assert 'codigo_dre' in serializer.data
        assert 'nome_dre' in serializer.data
        assert 'sigla_dre' in serializer.data
        assert serializer.data['codigo_dre'] == '001'


class TestUnidadeSerializer:
    """Testes para o UnidadeSerializer"""
    
    def test_serializer_com_dados_completos(self, dados_unidade_completos):
        """Testa serialização com todos os campos"""
        serializer = UnidadeSerializer(data=dados_unidade_completos)
        assert serializer.is_valid(), serializer.errors
        assert serializer.validated_data['codigoEol'] == '123456'
        assert serializer.validated_data['email'] == 'escola@exemplo.com'
        assert serializer.validated_data['cep'] == 12345678
    
    def test_serializer_com_dados_minimos(self, dados_unidade_minimos):
        """Testa serialização apenas com campos obrigatórios"""
        serializer = UnidadeSerializer(data=dados_unidade_minimos)
        assert serializer.is_valid(), serializer.errors
        assert serializer.validated_data['codigoEol'] == '123456'
        assert serializer.validated_data['nomeOficial'] == 'Escola Municipal'
    
    def test_campos_obrigatorios_faltando(self):
        """Testa validação quando faltam campos obrigatórios"""
        data = {'codigo_eol': '123456'}
        
        serializer = UnidadeSerializer(data=data)
        assert not serializer.is_valid()
        assert 'nome_oficial' in serializer.errors
        assert 'tipo_unidade_admin' in serializer.errors
        assert 'tipo_ue' in serializer.errors
        assert 'nome_dre' in serializer.errors
    
    @pytest.mark.parametrize('email_invalido', [
        'email_invalido',
        'sem@dominio',
        '@semlocal.com',
        'espacos no meio@email.com'
    ])
    def test_email_invalido(self, dados_unidade_minimos, email_invalido):
        """Testa validação de emails inválidos"""
        dados_unidade_minimos['email'] = email_invalido
        serializer = UnidadeSerializer(data=dados_unidade_minimos)
        assert not serializer.is_valid()
        assert 'email' in serializer.errors
    
    def test_email_vazio_permitido(self, dados_unidade_minimos):
        """Testa que email vazio é permitido"""
        dados_unidade_minimos['email'] = ''
        serializer = UnidadeSerializer(data=dados_unidade_minimos)
        assert serializer.is_valid(), serializer.errors
    
    def test_campos_numericos_null(self, dados_unidade_minimos):
        """Testa que campos numéricos opcionais aceitam null"""
        dados_unidade_minimos.update({
            'cep': None,
            'ano_construcao': None,
            'capacidade_vagas_total': None
        })
        
        serializer = UnidadeSerializer(data=dados_unidade_minimos)
        assert serializer.is_valid(), serializer.errors
    
    def test_output_com_source_mapping(self, dados_unidade_completos_camelcase):
        """Testa se o output usa os nomes padronizados"""
        serializer = UnidadeSerializer(dados_unidade_completos_camelcase)
        data = serializer.data
        
        campos_esperados = [
            'codigo_eol', 'nome_oficial', 'tipo_unidade_admin',
            'tipo_ue', 'nome_dre', 'capacidade_vagas_total', 'organizacao_parceira'
        ]
        
        for campo in campos_esperados:
            assert campo in data
    
    def test_tipo_nome_ue_com_dados_completos(self, dados_unidade_completos_camelcase):
        """Testa o campo customizado tipo_nome_ue"""
        serializer = UnidadeSerializer(dados_unidade_completos_camelcase)
        assert 'tipo_nome_ue' in serializer.data
        assert serializer.data['tipo_nome_ue'] == 'EMEF Escola Municipal de Ensino Fundamental'
    
    @pytest.mark.parametrize('tipo_ue,esperado', [
        ('', None),
        ('  EMEF  ', 'EMEF Escola Municipal'),
        ('CEI', 'CEI Escola Municipal'),
    ])
    def test_tipo_nome_ue_variantes(self, dados_unidade_minimos_camelcase, tipo_ue, esperado):
        """Testa tipo_nome_ue com diferentes valores de tipoUE"""
        dados_unidade_minimos_camelcase['tipoUE'] = tipo_ue
        serializer = UnidadeSerializer(dados_unidade_minimos_camelcase)
        assert serializer.data['tipo_nome_ue'] == esperado
    
    def test_campos_string_vazios_permitidos(self, dados_unidade_minimos):
        """Testa que campos string opcionais aceitam valores vazios"""
        dados_unidade_minimos.update({
            'nome_nao_oficial': '',
            'logradouro': '',
            'bairro': '',
            'telefone1': ''
        })
        
        serializer = UnidadeSerializer(data=dados_unidade_minimos)
        assert serializer.is_valid(), serializer.errors
    
    def test_capacidades_vagas_valores_validos(self, dados_unidade_minimos):
        """Testa valores válidos para capacidades de vagas"""
        dados_unidade_minimos.update({
            'capacidade_vagas_matutino': 100,
            'capacidade_vagas_vespertino': 150,
            'capacidade_vagas_noturno': 50,
            'capacidade_vagas_total': 300
        })
        
        serializer = UnidadeSerializer(data=dados_unidade_minimos)
        assert serializer.is_valid(), serializer.errors
        assert serializer.validated_data['capacidadeVagasMatutino'] == 100
        assert serializer.validated_data['capacidadeVagasTotal'] == 300
    
    @pytest.mark.parametrize('valor', [True, False])
    def test_organizacao_parceira_boolean(self, dados_unidade_minimos, valor):
        """Testa campo booleano organizacao_parceira"""
        dados_unidade_minimos['organizacao_parceira'] = valor
        serializer = UnidadeSerializer(data=dados_unidade_minimos)
        assert serializer.is_valid(), serializer.errors
        assert serializer.validated_data['organizacaoParceira'] is valor