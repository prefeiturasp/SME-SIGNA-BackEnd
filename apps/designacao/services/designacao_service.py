"""Serviço de designação.

Gerencia a criação, atualização e consulta de cargos pareados para atos de
designação.
"""

from django.db import transaction
from django.db.models import F, QuerySet
from rest_framework.exceptions import ValidationError

from apps.designacao.constants.cargos_gestao_escolar import (
    CODIGOS_CARGO_PROFESSOR,
)
from apps.designacao.models.ato_administrativo import AtoAdministrativo
from apps.designacao.models.designacao_detalhe import DesignacaoDetalhe

_CAMPOS_ATO = frozenset(
    {
        "numero_portaria",
        "ano_vigente",
        "sei_numero",
        "doc",
        "criado_por",
        "texto_sei",
        "modelo_portaria",
    }
)

# Regras de substituição do Diretor de Escola: período formal de 16 a 30
# dias (inclusivos); acima disso é necessária eleição para o cargo.
_SUBSTITUICAO_DIRETOR_MIN_DIAS = 16
_SUBSTITUICAO_DIRETOR_MAX_DIAS = 30
_CAMPOS_SUBSTITUICAO_DIRETOR = frozenset(
    {
        "cargo_vaga",
        "data_inicio",
        "data_fim",
        "indicado_codigo_cargo_base",
        "indicado_codigo_cargo_sobreposto",
        "indicado_possui_cargo_sobreposto",
        "indicado_codigo_ue_lotacao",
        "ue",
    }
)

# Códigos de erro das regras de substituição do Diretor, expostos em
# `codes` na resposta para o front diferenciar os bloqueios.
CODIGO_ELEICAO_NECESSARIA = "eleicao_necessaria"
CODIGO_PERIODO_INSUFICIENTE = "periodo_insuficiente"
CODIGO_UNIDADE_DIFERENTE = "unidade_diferente"

# Campos que representam o texto congelado da portaria — uma vez que o
# ato é publicado no Diário Oficial (doc preenchido), esse texto passa a
# ser um registro histórico e não pode mais ser reescrito.
_CAMPOS_TEXTO_PORTARIA = frozenset({"texto_sei", "modelo_portaria"})


class DesignacaoService:
    """Serviço de negócio para atos de designação."""

    @classmethod
    def criar(cls, data: dict) -> AtoAdministrativo:
        """Cria um ato administrativo de designação.

        Args:
            data: Dicionário com os dados do ato e do detalhe de designação.

        Returns:
            AtoAdministrativo: Ato administrativo de designação criado.

        """
        data_ato = {k: v for k, v in data.items() if k in _CAMPOS_ATO}
        data_detalhe = {k: v for k, v in data.items() if k not in _CAMPOS_ATO}

        cls._validar_substituicao_diretor(data_detalhe)

        with transaction.atomic():
            ato = AtoAdministrativo.objects.create(
                tipo=AtoAdministrativo.Tipo.DESIGNACAO,
                status_publicacao=AtoAdministrativo.StatusPublicacao.NAO_PUBLICADO,
                **data_ato,
            )
            DesignacaoDetalhe.objects.create(ato=ato, **data_detalhe)

        return ato

    @classmethod
    def atualizar(
        cls, ato: AtoAdministrativo, data: dict
    ) -> AtoAdministrativo:
        """Atualiza um ato administrativo de designação e seu detalhe.

        Args:
            ato: Ato administrativo de designação existente.
            data: Dicionário com os campos a atualizar.

        Returns:
            AtoAdministrativo: Ato administrativo atualizado.

        """
        data_ato = {k: v for k, v in data.items() if k in _CAMPOS_ATO}
        data_detalhe = {k: v for k, v in data.items() if k not in _CAMPOS_ATO}

        if _CAMPOS_TEXTO_PORTARIA & data_ato.keys() and ato.esta_publicado:
            raise ValidationError(
                {
                    "texto_sei": (
                        "Não é possível alterar o texto da portaria de um "
                        "ato já publicado no Diário Oficial."
                    )
                }
            )

        if _CAMPOS_SUBSTITUICAO_DIRETOR & data_detalhe.keys():
            detalhe_atual = ato.designacao_detalhe
            dados_efetivos = {
                campo: getattr(detalhe_atual, campo)
                for campo in _CAMPOS_SUBSTITUICAO_DIRETOR
            }
            dados_efetivos.update(data_detalhe)
            cls._validar_substituicao_diretor(dados_efetivos)

        with transaction.atomic():
            if data_ato:
                for field, value in data_ato.items():
                    setattr(ato, field, value)
                ato.save(update_fields=list(data_ato.keys()))

            if data_detalhe:
                detalhe = ato.designacao_detalhe
                for field, value in data_detalhe.items():
                    setattr(detalhe, field, value)
                detalhe.save(update_fields=list(data_detalhe.keys()))

        return ato

    @staticmethod
    def _validar_substituicao_diretor(dados: dict) -> None:
        """Valida as regras de designação para substituição do Diretor.

        Aplica-se quando a vaga é de Diretor de Escola: o período deve ter
        de 16 a 30 dias (acima disso é necessária eleição) e, se o indicado
        for professor, ele deve ser da mesma unidade escolar. O cargo do
        indicado (código EOL) é o cargo sobreposto, quando houver, ou o
        cargo base (função/atividade é ignorada), e é professor se estiver
        em `CODIGOS_CARGO_PROFESSOR`; a unidade
        é comparada pelo código da UE de lotação do indicado contra o
        código da UE da designação.

        Args:
            dados: Campos do detalhe de designação (valores efetivos).

        Raises:
            ValidationError: Se alguma regra de substituição for violada.

        """
        if dados.get("cargo_vaga") != DesignacaoDetalhe.CargoVaga.DIRETOR:
            return

        data_inicio = dados.get("data_inicio")
        data_fim = dados.get("data_fim")
        dias = (
            (data_fim - data_inicio).days + 1
            if data_inicio and data_fim
            else None
        )

        if dias is None or dias > _SUBSTITUICAO_DIRETOR_MAX_DIAS:
            raise ValidationError(
                {
                    "data_fim": [
                        "A substituição do Diretor não pode ultrapassar "
                        f"{_SUBSTITUICAO_DIRETOR_MAX_DIAS} dias. É "
                        "necessária a realização de eleição para o cargo "
                        "de Diretor."
                    ]
                },
                code=CODIGO_ELEICAO_NECESSARIA,
            )

        if dias < _SUBSTITUICAO_DIRETOR_MIN_DIAS:
            raise ValidationError(
                {
                    "data_fim": [
                        "A designação para substituição do Diretor deve "
                        f"ter período de {_SUBSTITUICAO_DIRETOR_MIN_DIAS} a "
                        f"{_SUBSTITUICAO_DIRETOR_MAX_DIAS} dias."
                    ]
                },
                code=CODIGO_PERIODO_INSUFICIENTE,
            )

        # Função/atividade não muda o cargo: só o cargo sobreposto
        # prevalece sobre o cargo base.
        codigo_cargo_indicado = (
            dados.get("indicado_codigo_cargo_sobreposto")
            if dados.get("indicado_possui_cargo_sobreposto")
            else dados.get("indicado_codigo_cargo_base")
        )
        eh_professor = codigo_cargo_indicado in CODIGOS_CARGO_PROFESSOR
        # Zeros à esquerda são ignorados: o EOL pode devolver o código
        # como número ("90450") ou texto ("090450").
        codigo_lotacao = str(dados.get("indicado_codigo_ue_lotacao") or "")
        codigo_ue = str(dados.get("ue") or "")
        if eh_professor and (
            not codigo_ue.strip().lstrip("0")
            or codigo_lotacao.strip().lstrip("0")
            != codigo_ue.strip().lstrip("0")
        ):
            raise ValidationError(
                {
                    "indicado_codigo_ue_lotacao": [
                        "O professor designado para substituir o Diretor "
                        "deve ser da mesma unidade escolar."
                    ]
                },
                code=CODIGO_UNIDADE_DIFERENTE,
            )

    @staticmethod
    def excluir(ato: AtoAdministrativo) -> None:
        """Remove um ato administrativo de designação.

        Impede a exclusão quando existirem atos derivados (cessação,
        apostila ou insubsistência) associados a esta designação, já que
        essas referências são protegidas contra exclusão em cascata.

        Args:
            ato: Ato administrativo de designação a ser removido.

        Raises:
            ValidationError: Se existirem atos derivados associados a
            esta designação.

        """
        tipos_dependentes = (
            ato.descendentes.order_by("tipo")
            .values_list("tipo", flat=True)
            .distinct()
        )
        if tipos_dependentes:
            labels = ", ".join(
                AtoAdministrativo.Tipo(tipo).label
                for tipo in tipos_dependentes
            )
            raise ValidationError(
                {
                    "detail": "Não é possível excluir esta designação: "
                    f"existem atos derivados ({labels}) associados a ela. "
                    "Exclua-os primeiro."
                }
            )
        ato.delete()

    @staticmethod
    def get_cargos_pareados(
        queryset: QuerySet,
        cod1: str,
        nome1: str,
        cod2: str,
        nome2: str,
    ) -> list:
        """Retorna cargos pareados a partir de um queryset.

        Args:
            queryset: QuerySet com os dados de cargos.
            cod1: Nome do campo de código do primeiro cargo.
            nome1: Nome do campo de nome do primeiro cargo.
            cod2: Nome do campo de código do segundo cargo.
            nome2: Nome do campo de nome do segundo cargo.

        Returns:
            list: Lista de cargos pareados ordenados por nome.

        """
        qs1 = (
            queryset.values(codigo=F(cod1), nome=F(nome1))
            .filter(**{f"{cod1}__isnull": False})
            .exclude(**{nome1: ""})
        )
        qs2 = (
            queryset.values(codigo=F(cod2), nome=F(nome2))
            .filter(**{f"{cod2}__isnull": False})
            .exclude(**{nome2: ""})
        )

        resultado = [
            {"codigoCargo": item["codigo"], "nomeCargo": item["nome"]}
            for item in qs1.union(qs2)
            if item["nome"]
        ]
        resultado.sort(key=lambda x: x["nomeCargo"])
        return resultado
