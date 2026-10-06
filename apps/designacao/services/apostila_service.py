"""Serviço de apostila.

Contém regras para criação de apostilas, incluindo validações e aplicação
de alterações em atos administrativos.
"""

import datetime
from dataclasses import dataclass, field
from typing import Any, NotRequired, TypedDict

from django.core.exceptions import FieldDoesNotExist
from django.core.exceptions import ValidationError as DjangoValidationError
from django.db import transaction
from django.db.models import (
    BooleanField,
    CharField,
    DateField,
    Field,
    ForeignKey,
    Model,
    QuerySet,
    TextField,
)
from rest_framework.exceptions import ValidationError

from apps.designacao.models.apostila_detalhe import (
    ApostilaAlteracao,
    ApostilaDetalhe,
)
from apps.designacao.models.ato_administrativo import AtoAdministrativo

_CAMPOS_ATO = frozenset(
    {
        "numero_portaria",
        "sei_numero",
        "doc",
        "ano_vigente",
        "criado_por",
        "texto_sei",
        "modelo_portaria",
    }
)
_CAMPOS_PROTEGIDOS = frozenset(
    {
        "id",
        "tipo",
        "ato_pai",
        "ato_pai_id",
        "ato_raiz",
        "ato_raiz_id",
        "criado_em",
    }
)
_CAMPOS_EXCLUIDOS_DETALHE = frozenset({"ato_id", "ato"})

# Campos que representam o texto congelado da portaria — quando
# ato alvo é publicado no Diário Oficial , esse texto
# passa a ser um registro histórico e nao pode mais ser editado via apostila.
_CAMPOS_TEXTO_PORTARIA = frozenset({"texto_sei", "modelo_portaria"})

_CAMPOS_DEPENDENTES = {
    "possui_pendencia": "pendencias",
    "com_afastamento": "motivo_afastamento",
}

_ROTULOS_CAMPOS = {
    "data_inicio": "A partir de",
    "data_fim": "Até (data final)",
    "pendencias": "Descrição da pendência",
    "possui_pendencia": "Possui pendência?",
    "motivo_afastamento": "Motivo do afastamento",
    "com_afastamento": "Com afastamento?",
    "impedimento_substituicao": "Impedimento para substituição",
    "carater_excepcional": "Caráter excepcional",
    "data_cessacao": "Data da cessação",
}

_VALORES_VERDADEIROS = frozenset({"true", "1", "t", "sim"})
_VALORES_FALSOS = frozenset({"false", "0", "f", "nao", "não"})


class CriarApostilaData(TypedDict):
    """Payload validado para criação de apostila no modelo legado."""

    designacao: int
    ato_apostilado: str
    tipo: str
    sei_numero: str
    observacao: str
    d_o: NotRequired[str]


@dataclass
class _PlanoAplicacao:
    """Acumula o efeito de uma apostila antes de gravar no banco."""

    originais: dict[tuple[int, str], ApostilaAlteracao] = field(
        default_factory=dict
    )
    detalhes_por_ato: dict[int, Model | None] = field(default_factory=dict)
    buckets: dict[tuple[int, str], dict[str, Any]] = field(
        default_factory=dict
    )
    atos_por_pk: dict[int, AtoAdministrativo] = field(default_factory=dict)
    registros_novos: list[ApostilaAlteracao] = field(default_factory=list)
    ids_excluir: set[int] = field(default_factory=set)
    atualizacoes: dict[int, ApostilaAlteracao] = field(default_factory=dict)


class ApostilaService:
    """Serviço de negócio para manipular apostilas."""

    # ── Querysets ────────────────────────────────────────────────────────────

    @staticmethod
    def listar() -> QuerySet:
        """Retorna queryset de apostilas (AtoAdministrativo)."""
        return (
            AtoAdministrativo.objects.filter(
                tipo=AtoAdministrativo.Tipo.APOSTILA
            )
            .select_related(
                "apostila_detalhe",
                "ato_pai__designacao_detalhe",
                "ato_raiz__designacao_detalhe",
                "ato_pai__cessacao_detalhe",
            )
            .prefetch_related(
                "apostila_detalhe__alteracoes",
                "filhos",
                "filhos__insubsistencia_detalhe",
            )
            .order_by("-criado_em")
        )

    @staticmethod
    def buscar(pk: int) -> AtoAdministrativo | None:
        """Retorna uma apostila por pk com todos os prefetches."""
        return ApostilaService.listar().filter(pk=pk).first()

    @staticmethod
    def criar(data: dict) -> AtoAdministrativo:
        """Cria um ato administrativo do tipo apostila.

        Args:
            data: Dicionário com os dados do ato e alterações associadas.

        Returns:
            AtoAdministrativo: Ato administrativo de apostila criado.

        Raises:
            ValidationError: Se o ato pai for inválido ou não puder ser
            apostilado.

        """
        ato_pai: AtoAdministrativo = data["ato_pai"]
        alteracoes: list = data.get("alteracoes", [])

        if not ato_pai.eh_valido:
            raise ValidationError({"ato_pai": "Este ato está insubsistente."})

        if ato_pai.filhos.exists():
            filhos = ato_pai.filhos.all()
            for filho in filhos:
                if (
                    filho.tipo == AtoAdministrativo.Tipo.APOSTILA
                    and filho.eh_valido
                ):
                    raise ValidationError(
                        {"ato_pai": "Este ato já foi apostilado."}
                    )

        if ato_pai.tipo == AtoAdministrativo.Tipo.DESIGNACAO:
            tem_cessacao_ativa = ato_pai.filhos.filter(
                tipo=AtoAdministrativo.Tipo.CESSACAO, ativo=True
            ).exists()
            if tem_cessacao_ativa:
                raise ValidationError(
                    {
                        "ato_pai": "Não é possível apostilar uma designação cessada."  # noqa: E501
                    }
                )

            detalhe = getattr(ato_pai, "designacao_detalhe", None)
            if (
                detalhe
                and detalhe.data_fim
                and detalhe.data_fim < datetime.date.today()
            ):
                raise ValidationError(
                    {
                        "ato_pai": "Não é possível apostilar uma designação com prazo finalizado."  # noqa: E501
                    }
                )

        data_ato = {k: v for k, v in data.items() if k in _CAMPOS_ATO}

        with transaction.atomic():
            ato = AtoAdministrativo.objects.create(
                tipo=AtoAdministrativo.Tipo.APOSTILA,
                status_publicacao=(
                    AtoAdministrativo.StatusPublicacao.NAO_PUBLICADO
                ),
                ato_pai=ato_pai,
                **data_ato,
            )
            apostila_detalhe = ApostilaDetalhe.objects.create(
                ato=ato,
                observacao=data["observacao"],
            )

            if alteracoes:
                ApostilaService._aplicar_alteracoes(
                    ato_pai, apostila_detalhe, alteracoes
                )

        return ato

    @staticmethod
    def atualizar(ato: AtoAdministrativo, data: dict) -> AtoAdministrativo:
        """Atualiza um ato administrativo do tipo apostila.

        Args:
            ato: Ato administrativo de apostila existente.
            data: Dicionário somente com os dados do ato a ser atualizado.

        Returns:
            AtoAdministrativo: Ato administrativo de apostila criado.

        Raises:
            ValidationError: Se o ato pai for inválido ou não puder ser
            apostilado.

        """
        ato_pai: AtoAdministrativo | None = ato.ato_pai
        alteracoes: list = data.get("alteracoes", [])
        observacao: str = data.get("observacao", "")

        if ato_pai is None:
            raise ValidationError(
                {"ato_pai": "Esta apostila não possui uma designação pai."}
            )

        if not ato_pai.eh_valido:
            raise ValidationError({"ato_pai": "Este ato está insubsistente."})

        data_ato = {k: v for k, v in data.items() if k in _CAMPOS_ATO}

        with transaction.atomic():
            if data_ato:
                for field, value in data_ato.items():
                    setattr(ato, field, value)
                ato.save(update_fields=list(data_ato.keys()))

            apostila_detalhe = ApostilaDetalhe.objects.get(ato=ato)

            if "observacao" in data:
                apostila_detalhe.observacao = observacao
                apostila_detalhe.save(update_fields=["observacao"])

            if alteracoes:
                ApostilaService._aplicar_alteracoes(
                    ato_pai, apostila_detalhe, alteracoes
                )
        return ato

    @staticmethod
    def _resolver_ato_alvo(
        alt: dict, ato_pai: AtoAdministrativo
    ) -> AtoAdministrativo:
        """Resolve a qual ato administrativo uma alteração se aplica.

        Por padrão, uma alteração afeta o próprio `ato_pai` da apostila
        — mesmo comportamento de sempre. Quando a apostila é feita sobre
        uma cessação, também é possível corrigir campos da designação de
        origem dessa cessação, informando `tipo_ato_alvo="DESIGNACAO"`
        na alteração.

        Args:
            alt: Item da lista de alterações, já validado pelo serializer.
            ato_pai: Ato administrativo sobre o qual a apostila é criada.

        Returns:
            AtoAdministrativo: O ato que efetivamente receberá a alteração.

        Raises:
            ValidationError: Se `tipo_ato_alvo` não corresponder ao
            próprio `ato_pai` nem à sua designação de origem.

        """
        tipo_alvo = alt.get("tipo_ato_alvo") or ato_pai.tipo

        if tipo_alvo == ato_pai.tipo:
            return ato_pai

        if (
            tipo_alvo == AtoAdministrativo.Tipo.DESIGNACAO
            and ato_pai.tipo == AtoAdministrativo.Tipo.CESSACAO
        ):
            designacao_origem = ato_pai.ato_pai
            assert designacao_origem is not None
            return designacao_origem

        raise ValidationError(
            {
                "alteracoes": (
                    f"Não é possível alterar um ato do tipo '{tipo_alvo}' "
                    "a partir desta apostila."
                )
            }
        )

    @staticmethod
    def _encontrar_campo(
        campo: str,
        ato: AtoAdministrativo,
        detalhe: Model | None,
    ) -> tuple[str, Field]:
        """Encontra o campo a ser alterado no ato ou no detalhe.

        Args:
            campo: Nome do campo a ser alterado. Para chaves estrangeiras
                aceita tanto o nome (``impedimento_substituicao``) quanto
                a coluna (``impedimento_substituicao_id``).
            ato: Ato administrativo alvo da alteração.
            detalhe: Detalhe associado ao ato, se existir.

        Returns:
            tuple[str, Field]: Tupla com destino ('ato' ou 'detalhe') e o
            campo do model.

        Raises:
            ValidationError: Se o campo não existir no ato ou no detalhe.

        """
        candidatos: list[tuple[str, Model]] = [("ato", ato)]
        if detalhe is not None and campo not in _CAMPOS_EXCLUIDOS_DETALHE:
            candidatos.append(("detalhe", detalhe))

        for destino, obj in candidatos:
            try:
                model_field = obj._meta.get_field(campo)
            except FieldDoesNotExist:
                continue
            if isinstance(model_field, Field) and model_field.concrete:
                return destino, model_field
        raise ValidationError(
            {"alteracoes": f"Campo '{campo}' não encontrado no ato alvo."}
        )

    @staticmethod
    def _converter_valor(model_field: Field, valor: str) -> Any:
        """Converta o valor textual da alteração para o tipo do campo.

        Args:
            model_field: Campo do model que receberá o valor.
            valor: Valor informado na apostila (vazio limpa o campo).

        Returns:
            Valor convertido, pronto para ser atribuído ao campo.

        Raises:
            ValidationError: Se o valor for inválido para o campo, com uma
            mensagem que identifica o campo para o usuário.

        """
        rotulo = _ROTULOS_CAMPOS.get(
            model_field.name, str(model_field.verbose_name)
        )

        def _erro(motivo: str) -> ValidationError:
            return ValidationError(
                {"alteracoes": f"Valor inválido para '{rotulo}': {motivo}"}
            )

        if valor == "":
            if model_field.null:
                return None
            if isinstance(model_field, (CharField, TextField)):
                return ""
            raise _erro("o campo é obrigatório.")

        if isinstance(model_field, BooleanField):
            normalizado = valor.strip().lower()
            if normalizado in _VALORES_VERDADEIROS:
                return True
            if normalizado in _VALORES_FALSOS:
                return False
            raise _erro("informe verdadeiro ou falso.")

        if isinstance(model_field, ForeignKey):
            modelo_relacionado = model_field.related_model
            try:
                pk = int(valor)
            except (TypeError, ValueError):
                raise _erro("informe uma opção válida.") from None
            assert not isinstance(modelo_relacionado, str)
            if not modelo_relacionado._default_manager.filter(pk=pk).exists():
                raise _erro("a opção selecionada não existe.")
            return pk

        try:
            convertido = model_field.to_python(valor)
            model_field.run_validators(convertido)
        except DjangoValidationError as exc:
            if isinstance(model_field, DateField):
                raise _erro(
                    "data inválida, use o formato AAAA-MM-DD."
                ) from None
            raise _erro(" ".join(exc.messages)) from None
        return convertido

    @staticmethod
    def _expandir_dependentes(alteracoes: list) -> list:
        """Inclui a limpeza dos textos que dependem de uma flag booleana.

        Quando ``possui_pendencia``/``com_afastamento`` é alterado para
        falso, a descrição da pendência / motivo do afastamento também é
        apagada — mesmo que o front não envie essa alteração. Como a
        limpeza vira uma ``ApostilaAlteracao``, a insubsistência da
        apostila restaura o texto original.

        Args:
            alteracoes: Lista de alterações recebida.

        Returns:
            list: Nova lista com as alterações dependentes ajustadas.

        """
        resultado = [dict(alt) for alt in alteracoes]
        for alt in list(resultado):
            dependente = _CAMPOS_DEPENDENTES.get(alt["campo_alterado"])
            if dependente is None:
                continue
            valor = str(alt.get("valor_novo") or "").strip().lower()
            if valor not in _VALORES_FALSOS:
                continue
            alvo = alt.get("tipo_ato_alvo") or ""
            existentes = [
                a
                for a in resultado
                if a["campo_alterado"] == dependente
                and (a.get("tipo_ato_alvo") or "") == alvo
            ]
            if existentes:
                for existente in existentes:
                    existente["valor_novo"] = ""
            else:
                resultado.append(
                    {
                        "campo_alterado": dependente,
                        "valor_novo": "",
                        "tipo_ato_alvo": alvo,
                    }
                )
        return resultado

    @staticmethod
    def _aplicar_alteracoes(
        ato_pai: AtoAdministrativo,
        apostila_detalhe: ApostilaDetalhe,
        alteracoes: list,
    ) -> None:
        """Aplica as alterações de uma apostila aos atos alvo.

        Cada alteração é resolvida individualmente contra seu ato alvo
        (o `ato_pai` da apostila, ou — quando indicado — a designação de
        origem dele), permitindo que uma mesma apostila corrija campos
        de mais de um ato na cadeia.

        Args:
            ato_pai: Ato administrativo original que está sendo apostilado.
            apostila_detalhe: Registro de detalhe da apostila.
            alteracoes: Lista de alterações a serem aplicadas.

        """
        plano = _PlanoAplicacao(
            originais={
                (registro.ato_alterado_id, registro.campo_alterado): registro
                for registro in ApostilaAlteracao.objects.filter(
                    apostila_id=apostila_detalhe.ato_id
                )
            }
        )
        # gera as alterações de designaçao e cessação e apostila
        for alt in ApostilaService._expandir_dependentes(alteracoes):
            ApostilaService._acumular_alteracao(
                alt, ato_pai, apostila_detalhe, plano
            )

        # persiste as alterações de designaçao e cessação no banco de dados
        for (ato_pk, destino), updates in plano.buckets.items():
            alvo = ApostilaService._alvo_do_bucket(ato_pk, destino, plano)
            ApostilaService._salvar_updates(alvo, updates)

        # persiste as alterações de apostila no banco de dados
        if plano.ids_excluir:
            ApostilaAlteracao.objects.filter(pk__in=plano.ids_excluir).delete()
        if plano.atualizacoes:
            ApostilaAlteracao.objects.bulk_update(
                list(plano.atualizacoes.values()), ["valor_novo"]
            )
        ApostilaAlteracao.objects.bulk_create(plano.registros_novos)

    @staticmethod
    def _acumular_alteracao(
        alt: dict,
        ato_pai: AtoAdministrativo,
        apostila_detalhe: ApostilaDetalhe,
        plano: _PlanoAplicacao,
    ) -> None:
        """Classifica uma alteração e acumula o efeito no plano.

        Registros já gravados são marcados para exclusão quando o valor
        volta ao original, ou para atualização de ``valor_novo``.
        Campos inéditos entram na lista de criação.

        Args:
            alt: Item da lista de alterações.
            ato_pai: Ato sobre o qual a apostila é criada.
            apostila_detalhe: Detalhe da apostila que recebe o histórico.
            plano: Acumulador das gravações adiadas para o fim.

        """
        campo = alt["campo_alterado"]
        valor_informado = alt["valor_novo"]
        valor_informado = (
            "" if valor_informado is None else str(valor_informado)
        )

        if campo in _CAMPOS_PROTEGIDOS:
            raise ValidationError(
                {
                    "alteracoes": (
                        f"Campo '{campo}' não pode ser alterado "
                        "via apostila."
                    )
                }
            )

        ato_alvo = ApostilaService._resolver_ato_alvo(alt, ato_pai)
        plano.atos_por_pk[ato_alvo.pk] = ato_alvo

        if campo in _CAMPOS_TEXTO_PORTARIA and ato_alvo.esta_publicado:
            raise ValidationError(
                {
                    "alteracoes": (
                        "Não é possível alterar o texto da portaria de "
                        "um ato já publicado no Diário Oficial."
                    )
                }
            )

        if ato_alvo.pk not in plano.detalhes_por_ato:
            plano.detalhes_por_ato[ato_alvo.pk] = ApostilaService._get_detalhe(
                ato_alvo
            )
        detalhe_alvo = plano.detalhes_por_ato[ato_alvo.pk]

        destino, model_field = ApostilaService._encontrar_campo(
            campo, ato_alvo, detalhe_alvo
        )
        campo = model_field.attname
        obj_alvo = ato_alvo if destino == "ato" else detalhe_alvo
        raw_anterior = getattr(obj_alvo, campo)
        valor_anterior = "" if raw_anterior is None else str(raw_anterior)

        convertido = ApostilaService._converter_valor(
            model_field, valor_informado
        )
        valor_novo = "" if convertido is None else str(convertido)

        # Marca para atualização do campo de cessação ou designação
        plano.buckets.setdefault((ato_alvo.pk, destino), {})[
            campo
        ] = convertido

        # Marca para atualização do campo de apostila
        chave = (ato_alvo.id, campo)
        registro = plano.originais.get(chave)
        # Se o registro não existir, marca para criação de um novo registro
        if registro is None:
            plano.registros_novos.append(
                ApostilaAlteracao(
                    apostila=apostila_detalhe,
                    ato_alterado=ato_alvo,
                    campo_alterado=campo,
                    valor_anterior=valor_anterior,
                    valor_novo=valor_novo,
                )
            )
            return
        # Se o registro tem o valor anterior
        # igual ao valor novo, marca para exclusão
        if registro.valor_anterior == valor_novo:
            plano.ids_excluir.add(registro.pk)
            plano.atualizacoes.pop(registro.pk, None)
            plano.originais.pop(chave, None)
            return
        # Se o registro tem o valor anterior
        # diferente do valor novo, marca para atualização
        registro.valor_novo = valor_novo
        plano.atualizacoes[registro.pk] = registro

    @staticmethod
    def _alvo_do_bucket(
        ato_pk: int, destino: str, plano: _PlanoAplicacao
    ) -> Model:
        """Retorna o objeto que receberá as alterações de um bucket.

        Args:
            ato_pk: Chave do ato alvo.
            destino: ``ato`` ou ``detalhe``.
            plano: Acumulador com os atos e detalhes já resolvidos.

        Returns:
            Model: Instância do ato ou do detalhe a ser atualizado.

        """
        if destino == "ato":
            return plano.atos_por_pk[ato_pk]
        detalhe_para_update = plano.detalhes_por_ato[ato_pk]
        assert detalhe_para_update is not None
        return detalhe_para_update

    @staticmethod
    def _salvar_updates(obj: Model, updates: dict) -> None:
        """Aplica os updates em um objeto e salva em lote.

        Args:
            obj: Objeto Django cujos campos serão atualizados.
            updates: Dicionário campo-valor com as alterações.

        """
        for campo, valor in updates.items():
            setattr(obj, campo, valor)
        obj.save(update_fields=list(updates.keys()))

    @staticmethod
    def _get_detalhe(ato: AtoAdministrativo) -> Model | None:
        """Retorna o detalhe associado a um ato administrativo.

        Args:
            ato: Ato administrativo cujo detalhe será buscado.

        Returns:
            object | None: O detalhe associado ou None.

        """
        if ato.tipo == AtoAdministrativo.Tipo.DESIGNACAO:
            return getattr(ato, "designacao_detalhe", None)
        if ato.tipo == AtoAdministrativo.Tipo.CESSACAO:
            return getattr(ato, "cessacao_detalhe", None)
        return None
