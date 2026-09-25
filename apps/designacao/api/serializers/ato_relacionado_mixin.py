"""Mixin para consolidar dados de designacao e cessacao."""

from typing import Any

from apps.designacao.models.ato_administrativo import AtoAdministrativo
from apps.designacao.models.cessacao_detalhe import CessacaoDetalhe
from apps.designacao.models.designacao_detalhe import DesignacaoDetalhe

_CAMPOS_ATO = (
    "numero_portaria",
    "ano_vigente",
    "sei_numero",
    "doc",
)

_CAMPOS_DESIGNACAO = (
    "dre_nome",
    "dre",
    "indicado_rf",
    "indicado_vinculo",
    "indicado_nome_civil",
    "indicado_nome_servidor",
    "indicado_lotacao",
    "indicado_cargo_base",
    "indicado_cargo_sobreposto",
    "indicado_local_exercicio",
    "indicado_categoria",
    "tipo_vaga",
    "cargo_vaga",
    "titular_nome_civil",
    "titular_nome_servidor",
    "titular_rf",
    "titular_cargo_base",
    "titular_vinculo",
    "ue",
    "codigo_hierarquico",
    "data_inicio",
    "data_fim",
    "com_afastamento",
    "motivo_afastamento",
    "unidade_proponente",
    "carater_excepcional",
    "possui_pendencia",
    "pendencias",
)


def _spread(origem: Any, campos: tuple[str, ...]) -> dict[str, Any]:
    """Copia atributos nomeados para um dict, no estilo do spread do JS."""
    return {campo: getattr(origem, campo) for campo in campos}


class AtoRelacionadoMixin:
    """Compartilha helpers de serializacao de atos relacionados."""

    def _get_cessacao_detalhe(
        self, obj: AtoAdministrativo
    ) -> CessacaoDetalhe | None:
        """Retorna o CessacaoDetalhe do ato raiz (cessacao original)."""
        if obj.tipo == AtoAdministrativo.Tipo.CESSACAO:
            return getattr(obj, "cessacao_detalhe", None)

        pai = obj.ato_pai
        if pai and pai.tipo == AtoAdministrativo.Tipo.CESSACAO:
            return getattr(pai, "cessacao_detalhe", None)

        return None

    def _get_designacao_detalhe(
        self, obj: AtoAdministrativo
    ) -> DesignacaoDetalhe | None:
        """Retorna o DesignacaoDetalhe do ato raiz (designacao original)."""
        if obj.tipo == AtoAdministrativo.Tipo.DESIGNACAO:
            return getattr(obj, "designacao_detalhe", None)

        raiz = obj.ato_raiz or obj.ato_pai
        if raiz:
            return getattr(raiz, "designacao_detalhe", None)
        return None

    def _get_designacao_ato_administrativo(
        self, obj: AtoAdministrativo
    ) -> AtoAdministrativo | None:
        """Retorna o ato administrativo de designacao original."""
        if obj.tipo == AtoAdministrativo.Tipo.DESIGNACAO:
            return obj

        raiz = obj.ato_raiz or obj.ato_pai
        if raiz:
            return raiz
        return None

    def _get_cessacao_ato_administrativo(
        self, obj: AtoAdministrativo
    ) -> AtoAdministrativo | None:
        """Retorna o ato administrativo de cessacao relacionado."""
        if obj.tipo == AtoAdministrativo.Tipo.CESSACAO:
            return obj

        raiz = obj.ato_raiz
        pai = obj.ato_pai
        if pai and pai.tipo == AtoAdministrativo.Tipo.CESSACAO:
            return pai
        if raiz and raiz.tipo == AtoAdministrativo.Tipo.CESSACAO:
            return raiz
        return None

    def get_designacao(self, obj: AtoAdministrativo) -> dict[str, Any] | None:
        """Retorna os dados de designacao do ato ou do ato relacionado."""
        d = self._get_designacao_detalhe(obj)
        ato_designacao = self._get_designacao_ato_administrativo(obj)

        if d and ato_designacao is not None:
            detalhe_historico = d.detalhe_para_quadro_de_historico_por_ano
            return {
                "numero_portaria": ato_designacao.numero_portaria,
                "ano_vigente": ato_designacao.ano_vigente,
                "sei_numero": ato_designacao.sei_numero,
                "doc": ato_designacao.doc,
                "dre_nome": d.dre_nome,
                "dre": d.dre,
                "indicado_rf": d.indicado_rf,
                "indicado_vinculo": d.indicado_vinculo,
                "indicado_nome_civil": d.indicado_nome_civil,
                "indicado_nome_servidor": d.indicado_nome_servidor,
                "indicado_lotacao": d.indicado_lotacao,
                "indicado_cargo_base": d.indicado_cargo_base,
                "indicado_cargo_sobreposto": d.indicado_cargo_sobreposto,
                "indicado_local_exercicio": d.indicado_local_exercicio,
                "indicado_categoria": d.indicado_categoria,
                "tipo_vaga": d.tipo_vaga,
                "cargo_vaga": d.cargo_vaga,
                "titular_nome_civil": d.titular_nome_civil,
                "titular_nome_servidor": d.titular_nome_servidor,
                "titular_rf": d.titular_rf,
                "titular_cargo_base": d.titular_cargo_base,
                "titular_vinculo": d.titular_vinculo,
                "impedimento_display": (
                    d.impedimento_substituicao.descricao
                    if d.impedimento_substituicao
                    else None
                ),
                "impedimento_substituicao": d.impedimento_substituicao_id,
                "ue": d.ue,
                "codigo_hierarquico": d.codigo_hierarquico,
                "data_inicio": d.data_inicio,
                "data_fim": d.data_fim,
                "com_afastamento": d.com_afastamento,
                "motivo_afastamento": d.motivo_afastamento,
                "unidade_proponente": d.unidade_proponente,
                "carater_excepcional": d.carater_excepcional,
                "possui_pendencia": d.possui_pendencia,
                "pendencias": d.pendencias,
                "informacoes_adicionais": d.informacoes_adicionais,
                "detalhe_para_quadro_de_historico_por_ano": detalhe_historico,
            }
        return None

    def get_cessacao(self, obj: AtoAdministrativo) -> dict[str, Any] | None:
        """Retorna os dados de cessacao do ato ou do ato relacionado."""
        detalhe = self._get_cessacao_detalhe(obj)
        ato_cessacao = self._get_cessacao_ato_administrativo(obj)

        if detalhe and ato_cessacao is not None:
            return {
                "numero_portaria": ato_cessacao.numero_portaria,
                "ano_vigente": ato_cessacao.ano_vigente,
                "sei_numero": ato_cessacao.sei_numero,
                "doc": ato_cessacao.doc,
                "remocao": detalhe.remocao,
                "a_pedido": detalhe.a_pedido,
                "aposentadoria": detalhe.aposentadoria,
                "data_cessacao": detalhe.data_cessacao,
            }
        return None
