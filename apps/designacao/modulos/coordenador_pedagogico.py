import logging

logger = logging.getLogger(__name__)


class ModuloCoordenadorPedagogicoCalculator:
    """
    Regra de cálculo de módulo para o cargo:
    - 3379 (Coordenador Pedagógico)

    Baseado nas normas vigentes da SME.
    """

    CARGO_COORDENADOR_PEDAGOGICO = "3379"

    def calcular(self, _cargo: dict, informacoes_ue: dict) -> int:
        sigla_tipo = self._obter_sigla(informacoes_ue)
        dados_turmas = informacoes_ue.get("turmas") or {}
        por_turno = dados_turmas.get("por_turno") or {}
        qtd_classes = dados_turmas.get("total")
        tem_turno_noturno = por_turno.get("noite", 0) > 0
        qtd_turmas_noturno = por_turno.get("noite", 0)

        modulo_fixo = self._regra_modulo_fixo(sigla_tipo)
        if modulo_fixo is not None:
            return modulo_fixo

        if qtd_classes is None:
            return self._modulo_sem_classes(informacoes_ue)

        if sigla_tipo == "EMEI":
            return self._regra_emei(qtd_classes)

        if sigla_tipo in ("EMEF", "EMEBS"):
            return self._regra_emef(
                qtd_classes,
                tem_turno_noturno,
                qtd_turmas_noturno,
            )

        return 0

    def _obter_sigla(self, informacoes_ue: dict) -> str:
        return (informacoes_ue.get("siglaTipoEscola") or "").strip().upper()

    def _regra_modulo_fixo(self, sigla_tipo: str):
        regras = {
            "CEI": 1,
            "CEMEI": 2,
        }
        return regras.get(sigla_tipo)

    def _modulo_sem_classes(self, informacoes_ue: dict) -> int:
        logger.warning(
            "Cálculo de módulo para Coordenador Pedagógico requer "
            "quantidade de classes (UE %s).",
            informacoes_ue.get("codigoUE"),
        )
        return 0

    def _regra_emei(self, qtd_classes: int) -> int:
        return 1 if qtd_classes <= 20 else 2

    def _regra_emef(
        self,
        qtd_classes: int,
        tem_turno_noturno: bool,
        qtd_turmas_noturno: int,
    ) -> int:
        if qtd_classes <= 14:
            return 1

        if qtd_classes <= 35:
            if tem_turno_noturno and qtd_turmas_noturno >= 5:
                return 3
            return 2

        if qtd_classes <= 50:
            return 3

        return 4
