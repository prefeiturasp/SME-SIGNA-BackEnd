import datetime

from django.db import transaction
from rest_framework.exceptions import ValidationError

from apps.designacao.models.apostila import Apostila
from apps.designacao.models.designacao import Designacao
from apps.designacao.models.ato_administrativo import AtoAdministrativo
from apps.designacao.models.apostila_detalhe import ApostilaDetalhe, ApostilaAlteracao


_CAMPOS_ATO = frozenset({'sei_numero', 'doc'})
_CAMPOS_PROTEGIDOS = frozenset({'id', 'tipo', 'ato_pai', 'ato_pai_id', 'ato_raiz', 'ato_raiz_id', 'criado_em'})


class ApostilaService:

    # ── Legado (modelo Apostila) ───────────────────────────────────────────────

    @staticmethod
    def criar_apostila(data: dict) -> Apostila:
        designacao_id = data.pop("designacao")
        ato_apostilado = data.pop("ato_apostilado")

        designacao = Designacao.objects.filter(
            id=designacao_id,
            is_deleted=False
        ).select_related("cessacao").first()

        if not designacao:
            raise ValidationError("Designação não encontrada.")

        if ato_apostilado == "designacao":
            alvo_designacao = designacao
            alvo_cessacao = None

        elif ato_apostilado == "cessacao":
            cessacao = getattr(designacao, "cessacao", None)

            if not cessacao or cessacao.is_deleted:
                raise ValidationError(
                    "Não existe cessação válida para esta designação."
                )

            alvo_designacao = None
            alvo_cessacao = cessacao

        else:
            raise ValidationError("Tipo de ato inválido.")

        alvo = alvo_designacao or alvo_cessacao

        if alvo.is_deleted:
            raise ValidationError("Não é possível apostilar um ato deletado.")

        queryset = Apostila.objects.filter(
            is_deleted=False,
            tipo=Apostila.Tipo.APOSTILA
        )

        if alvo_designacao:
            queryset = queryset.filter(designacao=alvo_designacao)
        else:
            queryset = queryset.filter(cessacao=alvo_cessacao)

        apostilas_ativas = queryset.exclude(
            id__in=Apostila.objects.filter(
                tipo=Apostila.Tipo.ANULACAO,
                apostila_referencia__in=queryset,
            ).values_list("apostila_referencia_id", flat=True)
        )

        if apostilas_ativas.exists():
            raise ValidationError(
                "Já existe uma apostila válida para este ato."
            )

        return Apostila.objects.create(
            tipo=data.get("tipo"),
            designacao=alvo_designacao,
            cessacao=alvo_cessacao,
            sei_numero=data.get("sei_numero"),
            observacao=data.get("observacao"),
            d_o=data.get("d_o", ""),
        )

    # ── V2 (modelo AtoAdministrativo) ─────────────────────────────────────────

    @staticmethod
    def criar(data: dict) -> AtoAdministrativo:
        ato_pai: AtoAdministrativo = data['ato_pai']
        alteracoes: list = data.get('alteracoes', [])

        if not ato_pai.eh_valido:
            raise ValidationError({'ato_pai': 'Este ato está insubsistente.'})

        if ato_pai.tipo == AtoAdministrativo.Tipo.DESIGNACAO:
            tem_cessacao_ativa = ato_pai.filhos.filter(
                tipo=AtoAdministrativo.Tipo.CESSACAO, ativo=True
            ).exists()
            if tem_cessacao_ativa:
                raise ValidationError({'ato_pai': 'Não é possível apostilar uma designação cessada.'})

            detalhe = getattr(ato_pai, 'designacao_detalhe', None)
            if detalhe and detalhe.data_fim and detalhe.data_fim < datetime.date.today():
                raise ValidationError({'ato_pai': 'Não é possível apostilar uma designação com prazo finalizado.'})

        data_ato = {k: v for k, v in data.items() if k in _CAMPOS_ATO}

        with transaction.atomic():
            ato = AtoAdministrativo.objects.create(
                tipo=AtoAdministrativo.Tipo.APOSTILA,
                ato_pai=ato_pai,
                **data_ato,
            )
            apostila_detalhe = ApostilaDetalhe.objects.create(
                ato=ato,
                observacao=data['observacao'],
            )

            if alteracoes:
                ApostilaService._aplicar_alteracoes(ato_pai, apostila_detalhe, alteracoes)

        return ato

    @staticmethod
    def _aplicar_alteracoes(
        ato_pai: AtoAdministrativo,
        apostila_detalhe: ApostilaDetalhe,
        alteracoes: list,
    ) -> None:
        detalhe = ApostilaService._get_detalhe(ato_pai)

        ato_pai_updates = {}
        detalhe_updates = {}
        registros = []

        for alt in alteracoes:
            campo = alt['campo_alterado']
            valor_novo = str(alt['valor_novo'])

            if campo in _CAMPOS_PROTEGIDOS:
                raise ValidationError(
                    {'alteracoes': f"Campo '{campo}' não pode ser alterado via apostila."}
                )

            if hasattr(ato_pai, campo):
                raw = getattr(ato_pai, campo)
                valor_anterior = '' if raw is None else str(raw)
                ato_pai_updates[campo] = valor_novo
            elif detalhe and hasattr(detalhe, campo) and campo not in ('ato_id', 'ato'):
                raw = getattr(detalhe, campo)
                valor_anterior = '' if raw is None else str(raw)
                detalhe_updates[campo] = valor_novo
            else:
                raise ValidationError(
                    {'alteracoes': f"Campo '{campo}' não encontrado no ato pai."}
                )

            registros.append(ApostilaAlteracao(
                apostila=apostila_detalhe,
                campo_alterado=campo,
                valor_anterior=valor_anterior,
                valor_novo=valor_novo,
            ))

        if ato_pai_updates:
            ApostilaService._salvar_updates(ato_pai, ato_pai_updates)

        if detalhe_updates:
            ApostilaService._salvar_updates(detalhe, detalhe_updates)

        ApostilaAlteracao.objects.bulk_create(registros)

    @staticmethod
    def _salvar_updates(obj, updates: dict) -> None:
        for campo, valor in updates.items():
            setattr(obj, campo, valor)
        obj.save(update_fields=list(updates.keys()))

    @staticmethod
    def _get_detalhe(ato_pai: AtoAdministrativo):
        if ato_pai.tipo == AtoAdministrativo.Tipo.DESIGNACAO:
            return getattr(ato_pai, 'designacao_detalhe', None)
        if ato_pai.tipo == AtoAdministrativo.Tipo.CESSACAO:
            return getattr(ato_pai, 'cessacao_detalhe', None)
        return None
