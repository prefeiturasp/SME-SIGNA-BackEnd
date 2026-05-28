"""Serializadores de designação para API.

Conteúdos de leitura e escrita de designações, incluindo campos legados
relacionados a impedimento de substituição, portaria, servidor e período.
"""

from rest_framework import serializers

from apps.designacao.api.serializers.utils import NullableDateField
from apps.designacao.models.ato_administrativo import AtoAdministrativo
from apps.designacao.models.designacao import ImpedimentoSubstituicao
from apps.designacao.models.designacao_detalhe import DesignacaoDetalhe


class ImpedimentoSubstituicaoSerializer(serializers.ModelSerializer):
    """Serializador para impedimento de substituição.

    Representa o código e a descrição do impedimento em contexto de designação.
    """

    class Meta:
        model = ImpedimentoSubstituicao
        fields = ["id", "codigo", "descricao"]


# ── Escrita ──────────────────────────────────────────────────────────────────


class DesignacaoWriteSerializer(serializers.Serializer):
    """Serializador de escrita para criação/atualização de designações.

    Define os campos necessários para persistir um ato administrativo de
    designação,
    incluindo informações de unidade, servidor indicado, titular, período e
    vaga.
    """

    # AtoAdministrativo
    numero_portaria = serializers.CharField(max_length=20)
    ano_vigente = serializers.CharField(max_length=6)
    sei_numero = serializers.CharField(max_length=30)
    doc = NullableDateField(required=False, default=None, allow_null=True)

    # Unidade
    dre_nome = serializers.CharField(max_length=255)
    unidade_proponente = serializers.CharField(max_length=255)
    codigo_hierarquico = serializers.CharField(max_length=50)
    dre = serializers.CharField(
        max_length=50, required=False, default="", allow_blank=True
    )
    ue = serializers.CharField(
        max_length=50, required=False, default="", allow_blank=True
    )
    funcionarios_da_unidade = serializers.CharField(
        max_length=50, required=False, default="", allow_blank=True
    )

    # Indicado
    indicado_nome_civil = serializers.CharField(
        max_length=255, allow_blank=True
    )
    indicado_nome_servidor = serializers.CharField(max_length=255)
    indicado_rf = serializers.CharField(max_length=8)
    indicado_vinculo = serializers.IntegerField()
    indicado_cargo_base = serializers.CharField(max_length=255)
    indicado_codigo_cargo_base = serializers.IntegerField(
        required=False, allow_null=True
    )
    indicado_lotacao = serializers.CharField(max_length=255)
    indicado_cargo_sobreposto = serializers.CharField(
        max_length=255, required=False, default="", allow_blank=True
    )
    indicado_codigo_cargo_sobreposto = serializers.IntegerField(
        required=False, allow_null=True
    )
    indicado_local_exercicio = serializers.CharField(max_length=255)
    indicado_local_servico = serializers.CharField(
        max_length=255, required=False, default="", allow_blank=True
    )

    # Titular
    titular_nome_civil = serializers.CharField(
        max_length=255, required=False, default="", allow_blank=True
    )
    titular_nome_servidor = serializers.CharField(
        max_length=255, required=False, default="", allow_blank=True
    )
    titular_rf = serializers.CharField(
        max_length=8, required=False, default="", allow_blank=True
    )
    titular_vinculo = serializers.IntegerField(required=False, allow_null=True)
    titular_cargo_base = serializers.CharField(
        max_length=255, required=False, default="", allow_blank=True
    )
    titular_codigo_cargo_base = serializers.IntegerField(
        required=False, allow_null=True
    )
    titular_lotacao = serializers.CharField(
        max_length=255, required=False, default="", allow_blank=True
    )
    titular_cargo_sobreposto = serializers.CharField(
        max_length=255, required=False, default="", allow_blank=True
    )
    titular_codigo_cargo_sobreposto = serializers.IntegerField(
        required=False, allow_null=True
    )
    titular_local_exercicio = serializers.CharField(
        max_length=255, required=False, default="", allow_blank=True
    )
    titular_local_servico = serializers.CharField(
        max_length=255, required=False, default="", allow_blank=True
    )

    # Período
    data_inicio = serializers.DateField()
    data_fim = serializers.DateField(required=False, allow_null=True)

    # Flags
    carater_excepcional = serializers.BooleanField(
        required=False, default=False
    )
    com_afastamento = serializers.BooleanField(required=False, default=False)
    possui_pendencia = serializers.BooleanField(required=False, default=False)
    pendencias = serializers.CharField(
        required=False, default="", allow_blank=True
    )
    motivo_afastamento = serializers.CharField(
        required=False, default="", allow_blank=True
    )
    informacoes_adicionais = serializers.CharField(
        required=False, default="", allow_blank=True
    )
    detalhe_para_quadro_de_historico_por_ano = serializers.BooleanField(
        required=False, default=True
    )

    # Impedimento
    impedimento_substituicao = serializers.PrimaryKeyRelatedField(
        queryset=ImpedimentoSubstituicao.objects.all(),
        required=False,
        allow_null=True,
    )

    # Vaga
    tipo_vaga = serializers.ChoiceField(
        choices=DesignacaoDetalhe.TipoVaga.choices
    )
    cargo_vaga = serializers.ChoiceField(
        choices=DesignacaoDetalhe.CargoVaga.choices,
        required=False,
        allow_null=True,
    )


# ── Leitura ──────────────────────────────────────────────────────────────────


class DesignacaoReadSerializer(serializers.ModelSerializer):
    """Serializador de leitura para designações.

    Exibe dados de designação com campos relacionados ao detalhe de designação,
    incluindo campos derivados de filhos como cessação, apostilas e
    insubsistência.
    """

    status = serializers.SerializerMethodField()

    # Unidade
    dre_nome = serializers.CharField(
        source="designacao_detalhe.dre_nome", read_only=True
    )
    unidade_proponente = serializers.CharField(
        source="designacao_detalhe.unidade_proponente", read_only=True
    )
    codigo_hierarquico = serializers.CharField(
        source="designacao_detalhe.codigo_hierarquico", read_only=True
    )
    dre = serializers.CharField(
        source="designacao_detalhe.dre", read_only=True
    )
    ue = serializers.CharField(source="designacao_detalhe.ue", read_only=True)
    funcionarios_da_unidade = serializers.CharField(
        source="designacao_detalhe.funcionarios_da_unidade", read_only=True
    )

    # Indicado
    indicado_nome_civil = serializers.CharField(
        source="designacao_detalhe.indicado_nome_civil", read_only=True
    )
    indicado_nome_servidor = serializers.CharField(
        source="designacao_detalhe.indicado_nome_servidor", read_only=True
    )
    indicado_rf = serializers.CharField(
        source="designacao_detalhe.indicado_rf", read_only=True
    )
    indicado_vinculo = serializers.IntegerField(
        source="designacao_detalhe.indicado_vinculo", read_only=True
    )
    indicado_cargo_base = serializers.CharField(
        source="designacao_detalhe.indicado_cargo_base", read_only=True
    )
    indicado_codigo_cargo_base = serializers.IntegerField(
        source="designacao_detalhe.indicado_codigo_cargo_base",
        read_only=True,
        allow_null=True,
    )
    indicado_lotacao = serializers.CharField(
        source="designacao_detalhe.indicado_lotacao", read_only=True
    )
    indicado_cargo_sobreposto = serializers.CharField(
        source="designacao_detalhe.indicado_cargo_sobreposto", read_only=True
    )
    indicado_codigo_cargo_sobreposto = serializers.IntegerField(
        source="designacao_detalhe.indicado_codigo_cargo_sobreposto",
        read_only=True,
        allow_null=True,
    )
    indicado_local_exercicio = serializers.CharField(
        source="designacao_detalhe.indicado_local_exercicio", read_only=True
    )
    indicado_local_servico = serializers.CharField(
        source="designacao_detalhe.indicado_local_servico", read_only=True
    )

    # Titular
    titular_nome_civil = serializers.CharField(
        source="designacao_detalhe.titular_nome_civil", read_only=True
    )
    titular_nome_servidor = serializers.CharField(
        source="designacao_detalhe.titular_nome_servidor", read_only=True
    )
    titular_rf = serializers.CharField(
        source="designacao_detalhe.titular_rf", read_only=True
    )
    titular_vinculo = serializers.IntegerField(
        source="designacao_detalhe.titular_vinculo",
        read_only=True,
        allow_null=True,
    )
    titular_cargo_base = serializers.CharField(
        source="designacao_detalhe.titular_cargo_base", read_only=True
    )
    titular_codigo_cargo_base = serializers.IntegerField(
        source="designacao_detalhe.titular_codigo_cargo_base",
        read_only=True,
        allow_null=True,
    )
    titular_lotacao = serializers.CharField(
        source="designacao_detalhe.titular_lotacao", read_only=True
    )
    titular_cargo_sobreposto = serializers.CharField(
        source="designacao_detalhe.titular_cargo_sobreposto", read_only=True
    )
    titular_codigo_cargo_sobreposto = serializers.IntegerField(
        source="designacao_detalhe.titular_codigo_cargo_sobreposto",
        read_only=True,
        allow_null=True,
    )
    titular_local_exercicio = serializers.CharField(
        source="designacao_detalhe.titular_local_exercicio", read_only=True
    )
    titular_local_servico = serializers.CharField(
        source="designacao_detalhe.titular_local_servico", read_only=True
    )

    # Período
    data_inicio = serializers.DateField(
        source="designacao_detalhe.data_inicio", read_only=True
    )
    data_fim = serializers.DateField(
        source="designacao_detalhe.data_fim", read_only=True, allow_null=True
    )

    # Flags
    carater_excepcional = serializers.BooleanField(
        source="designacao_detalhe.carater_excepcional", read_only=True
    )
    com_afastamento = serializers.BooleanField(
        source="designacao_detalhe.com_afastamento", read_only=True
    )
    possui_pendencia = serializers.BooleanField(
        source="designacao_detalhe.possui_pendencia", read_only=True
    )
    pendencias = serializers.CharField(
        source="designacao_detalhe.pendencias", read_only=True
    )
    motivo_afastamento = serializers.CharField(
        source="designacao_detalhe.motivo_afastamento", read_only=True
    )
    informacoes_adicionais = serializers.CharField(
        source="designacao_detalhe.informacoes_adicionais", read_only=True
    )
    detalhe_para_quadro_de_historico_por_ano = serializers.BooleanField(
        source="designacao_detalhe.detalhe_para_quadro_de_historico_por_ano",
        read_only=True,
    )

    # Impedimento
    impedimento_substituicao = serializers.PrimaryKeyRelatedField(
        source="designacao_detalhe.impedimento_substituicao", read_only=True
    )
    impedimento_substituicao_detail = ImpedimentoSubstituicaoSerializer(
        source="designacao_detalhe.impedimento_substituicao", read_only=True
    )
    impedimento_display = serializers.SerializerMethodField()

    # Vaga
    tipo_vaga = serializers.CharField(
        source="designacao_detalhe.tipo_vaga", read_only=True
    )
    cargo_vaga = serializers.IntegerField(
        source="designacao_detalhe.cargo_vaga", read_only=True, allow_null=True
    )
    tipo_vaga_display = serializers.SerializerMethodField()
    cargo_vaga_display = serializers.SerializerMethodField()

    # Filhos (preenchidos com prefetch_related na view)
    cessacao = serializers.SerializerMethodField()
    apostilas = serializers.SerializerMethodField()
    insubsistencia = serializers.SerializerMethodField()

    class Meta:
        model = AtoAdministrativo
        fields = [
            "id",
            "tipo",
            "status",
            "ato_pai_id",
            "ato_raiz_id",
            "numero_portaria",
            "ano_vigente",
            "sei_numero",
            "doc",
            "criado_em",
            # Unidade
            "dre_nome",
            "unidade_proponente",
            "codigo_hierarquico",
            "dre",
            "ue",
            "funcionarios_da_unidade",
            # Indicado
            "indicado_nome_civil",
            "indicado_nome_servidor",
            "indicado_rf",
            "indicado_vinculo",
            "indicado_cargo_base",
            "indicado_codigo_cargo_base",
            "indicado_lotacao",
            "indicado_cargo_sobreposto",
            "indicado_codigo_cargo_sobreposto",
            "indicado_local_exercicio",
            "indicado_local_servico",
            # Titular
            "titular_nome_civil",
            "titular_nome_servidor",
            "titular_rf",
            "titular_vinculo",
            "titular_cargo_base",
            "titular_codigo_cargo_base",
            "titular_lotacao",
            "titular_cargo_sobreposto",
            "titular_codigo_cargo_sobreposto",
            "titular_local_exercicio",
            "titular_local_servico",
            # Período
            "data_inicio",
            "data_fim",
            # Flags
            "carater_excepcional",
            "com_afastamento",
            "possui_pendencia",
            "pendencias",
            "motivo_afastamento",
            "informacoes_adicionais",
            "detalhe_para_quadro_de_historico_por_ano",
            # Impedimento
            "impedimento_substituicao",
            "impedimento_substituicao_detail",
            "impedimento_display",
            # Vaga
            "tipo_vaga",
            "cargo_vaga",
            "tipo_vaga_display",
            "cargo_vaga_display",
            # Filhos
            "cessacao",
            "apostilas",
            "insubsistencia",
        ]

    def get_status(self, obj: AtoAdministrativo) -> str:
        """Retorna o status do ato administrativo.

        Args:
            obj: Instância de AtoAdministrativo.

        Returns:
            str: Status do ato.
        """
        return obj.status

    def get_impedimento_display(self, obj: AtoAdministrativo) -> str | None:
        """Retorna a descrição do impedimento de substituição.

        Args:
            obj: Instância de AtoAdministrativo.

        Returns:
            str|None: Descrição do impedimento ou None se não houver.
        """
        try:
            imp = obj.designacao_detalhe.impedimento_substituicao
            return imp.descricao if imp else None
        except Exception:
            return None

    def get_tipo_vaga_display(self, obj: AtoAdministrativo) -> str | None:
        """Retorna o texto descritivo do tipo de vaga.

        Args:
            obj: Instância de AtoAdministrativo.

        Returns:
            str|None: Descrição do tipo de vaga ou None em caso de erro.
        """
        try:
            return obj.designacao_detalhe.get_tipo_vaga_display()
        except Exception:
            return None

    def get_cargo_vaga_display(self, obj: AtoAdministrativo) -> str | None:
        """Retorna o texto descritivo do cargo da vaga.

        Args:
            obj: Instância de AtoAdministrativo.

        Returns:
            str|None: Descrição do cargo da vaga ou None em caso de erro.
        """
        try:
            return obj.designacao_detalhe.get_cargo_vaga_display()
        except Exception:
            return None

    def get_cessacao(self, obj: AtoAdministrativo) -> dict | None:
        """Retorna dados da cessação associada à designação.

        Args:
            obj: Instância de AtoAdministrativo.

        Returns:
            dict|None: Dados simplificados da cessação ou None se não existir.
        """
        # Usa filhos prefetchados (.all() aproveita o cache do prefetch_related)  # noqa: E501
        cessacao_ato = next(
            (
                f
                for f in obj.filhos.all()
                if f.tipo == AtoAdministrativo.Tipo.CESSACAO
            ),
            None,
        )
        if not cessacao_ato:
            return None
        try:
            d = cessacao_ato.cessacao_detalhe
            return {
                "id": cessacao_ato.id,
                "numero_portaria": cessacao_ato.numero_portaria,
                "ano_vigente": cessacao_ato.ano_vigente,
                "sei_numero": cessacao_ato.sei_numero,
                "doc": cessacao_ato.doc,
                "status": cessacao_ato.status,
                "a_pedido": d.a_pedido,
                "remocao": d.remocao,
                "aposentadoria": d.aposentadoria,
                "data_cessacao": d.data_cessacao,
                "criado_em": cessacao_ato.criado_em,
                "apostilas": self._serializar_apostilas(cessacao_ato),
                "insubsistencia": self._serializar_insubsistencia(
                    cessacao_ato
                ),
            }
        except Exception:
            return None

    def _serializar_insubsistencia(
        self, ato: AtoAdministrativo
    ) -> dict | None:
        """Serializa a insubsistência válida de um ato.

        Args:
            ato: Instância de AtoAdministrativo representando o ato pai.

        Returns:
            dict|None: Dados de insubsistência ou None se não houver ato
            válido.
        """
        insub = next(
            (
                f
                for f in ato.filhos.all()
                if f.tipo == AtoAdministrativo.Tipo.INSUBSISTENCIA
                and f.eh_valido
            ),
            None,
        )
        if not insub:
            return None
        try:
            d = insub.insubsistencia_detalhe
            return {
                "id": insub.id,
                "observacoes": d.observacoes,
            }
        except Exception:
            return None

    def _serializar_apostilas(self, ato: AtoAdministrativo) -> list:
        """Serializa apostilas relacionadas a um ato.

        Args:
            ato: Instância de AtoAdministrativo.

        Returns:
            list: Lista de apostilas serializadas.
        """
        resultado = []
        for f in ato.filhos.all():
            if f.tipo != AtoAdministrativo.Tipo.APOSTILA:
                continue
            try:
                d = f.apostila_detalhe
                resultado.append(
                    {
                        "id": f.id,
                        "sei_numero": f.sei_numero,
                        "doc": f.doc,
                        "status": f.status,
                        "observacao": d.observacao,
                        "criado_em": f.criado_em,
                    }
                )
            except Exception:
                pass
        return resultado

    def get_apostilas(self, obj: AtoAdministrativo) -> list:
        """Retorna as apostilas associadas ao ato.

        Args:
            obj: Instância de AtoAdministrativo.

        Returns:
            list: Lista de apostilas serializadas.
        """
        return self._serializar_apostilas(obj)

    def get_insubsistencia(self, obj: AtoAdministrativo) -> dict | None:
        """Retorna a insubsistência ativa da designação.

        Args:
            obj: Instância de AtoAdministrativo.

        Returns:
            dict|None: Dados da insubsistência ou None se não existir.
        """
        # Retorna a insubsistência que ainda está ativa (não foi tornada sem efeito)  # noqa: E501
        insub = next(
            (
                f
                for f in obj.filhos.all()
                if f.tipo == AtoAdministrativo.Tipo.INSUBSISTENCIA
                and f.eh_valido
            ),
            None,
        )
        if not insub:
            return None
        try:
            d = insub.insubsistencia_detalhe
            return {
                "id": insub.id,
                "numero_portaria": insub.numero_portaria,
                "ano_vigente": insub.ano_vigente,
                "sei_numero": insub.sei_numero,
                "doc": insub.doc,
                "observacoes": d.observacoes,
                "criado_em": insub.criado_em,
            }
        except Exception:
            return None
