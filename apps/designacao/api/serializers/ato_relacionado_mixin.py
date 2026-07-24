"""Mixin para consolidar dados de designacao e cessacao."""

from typing import Any

from apps.designacao.models.ato_administrativo import AtoAdministrativo
from apps.designacao.models.cessacao_detalhe import CessacaoDetalhe
from apps.designacao.models.designacao_detalhe import DesignacaoDetalhe


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
        detalhe = self._get_designacao_detalhe(obj)
        ato_designacao = self._get_designacao_ato_administrativo(obj)

        if detalhe and ato_designacao is not None:
            return {
                "numero_portaria": ato_designacao.numero_portaria,
                "ano_vigente": ato_designacao.ano_vigente,
                "sei_numero": ato_designacao.sei_numero,
                "doc": ato_designacao.doc,
                "dre_nome": detalhe.dre_nome,
                "indicado_rf": detalhe.indicado_rf,
                "indicado_vinculo": detalhe.indicado_vinculo,
                "indicado_nome_civil": detalhe.indicado_nome_civil,
                "indicado_nome_servidor": detalhe.indicado_nome_servidor,
                "indicado_lotacao": detalhe.indicado_lotacao,
                "indicado_cargo_base": detalhe.indicado_cargo_base,
                "indicado_cargo_sobreposto": detalhe.indicado_cargo_sobreposto,
                "indicado_local_exercicio": detalhe.indicado_local_exercicio,
                "indicado_categoria": detalhe.indicado_categoria,
                "tipo_vaga": detalhe.tipo_vaga,
                "titular_nome_civil": detalhe.titular_nome_civil,
                "titular_nome_servidor": detalhe.titular_nome_servidor,
                "titular_rf": detalhe.titular_rf,
                "titular_cargo_base": detalhe.titular_cargo_base,
                "titular_vinculo": detalhe.titular_vinculo,
                "impedimento_substituicao": (
                    detalhe.impedimento_substituicao.descricao
                    if detalhe.impedimento_substituicao
                    else None
                ),
                "ue": detalhe.ue,
                "codigo_hierarquico": detalhe.codigo_hierarquico,
                "data_inicio": detalhe.data_inicio,
                "data_fim": detalhe.data_fim,
                "com_afastamento": detalhe.com_afastamento,
                "motivo_afastamento": detalhe.motivo_afastamento,
                "pendencias": detalhe.pendencias,
                "unidade_proponente": detalhe.unidade_proponente,
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
