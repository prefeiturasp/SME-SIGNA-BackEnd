from rest_framework import serializers


class DRESerializer(serializers.Serializer):
    """Serializer para DREs com nomes padronizados"""
    codigo_dre = serializers.CharField(source='codigoDRE')
    nome_dre = serializers.CharField(source='nomeDRE')
    sigla_dre = serializers.CharField(source='siglaDRE')


class UnidadeSerializer(serializers.Serializer):
    """Serializer para Unidades Escolares com nomes padronizados"""
    codigo_eol = serializers.CharField(source='codigoEol')
    nome_oficial = serializers.CharField(source='nomeOficial')
    nome_nao_oficial = serializers.CharField(source='nomeNaoOficial', required=False, allow_blank=True)
    tipo_unidade_admin = serializers.CharField(source='tipoUnidadeAdmin')
    tipo_ue = serializers.CharField(source='tipoUE')
    logradouro = serializers.CharField(source='logadouro', required=False, allow_blank=True)
    numero = serializers.CharField(required=False, allow_blank=True)
    bairro = serializers.CharField(required=False, allow_blank=True)
    cep = serializers.IntegerField(required=False, allow_null=True)
    distrito = serializers.CharField(required=False, allow_blank=True)
    sub_prefeitura = serializers.CharField(source='subPrefeitura', required=False, allow_blank=True)
    nome_dre = serializers.CharField(source='nomeDre')
    email = serializers.EmailField(required=False, allow_blank=True)
    telefone1 = serializers.CharField(required=False, allow_blank=True)
    telefone2 = serializers.CharField(required=False, allow_blank=True)
    ano_construcao = serializers.IntegerField(source='anoConstrucao', required=False, allow_null=True)
    propriedade = serializers.CharField(required=False, allow_blank=True)
    capacidade_vagas_matutino = serializers.IntegerField(source='capacidadeVagasMatutino', required=False, allow_null=True)
    capacidade_vagas_vespertino = serializers.IntegerField(source='capacidadeVagasVespertino', required=False, allow_null=True)
    capacidade_vagas_noturno = serializers.IntegerField(source='capacidadeVagasNoturno', required=False, allow_null=True)
    capacidade_vagas_intermediario = serializers.IntegerField(source='capacidadeVagasIntermediario', required=False, allow_null=True)
    capacidade_vagas_integral = serializers.IntegerField(source='capacidadeVagasIntegral', required=False, allow_null=True)
    capacidade_vagas_total = serializers.IntegerField(source='capacidadeVagasTotal', required=False, allow_null=True)
    organizacao_parceira = serializers.BooleanField(source='organizacaoParceira', required=False)
    quantidade_funcionarios = serializers.IntegerField(source='quantidadeDeFuncionarios', required=False, allow_null=True)
    status = serializers.CharField(required=False, allow_blank=True)
    # Campo customizado
    tipo_nome_ue = serializers.SerializerMethodField()

    def get_tipo_nome_ue(self, obj):
        """Combina tipo e nome da UE"""
        tipo_ue = obj.get('tipoUE', '').strip()
        nome = obj.get('nomeOficial', '')
        if tipo_ue and nome:
            return f"{tipo_ue} {nome}"
        return None