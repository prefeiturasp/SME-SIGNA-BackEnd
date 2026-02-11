import logging

logger = logging.getLogger(__name__)


class ModuloCoordenadorPedagogicoCalculator:
    """
    Regra de cálculo de módulo para o cargo:
    - 3379 (Coordenador Pedagógico)

    Baseado nas normas vigentes da SME.
    """

    CARGO_COORDENADOR_PEDAGOGICO = "3379"

    def calcular(self, cargo: dict, informacoes_ue: dict) -> int:
        sigla_tipo = (informacoes_ue.get("siglaTipoEscola") or "").strip().upper()

        # --- PONTOS DE INTEGRAÇÃO FUTURA ---
        qtd_classes = informacoes_ue.get("quantidade_classes_api_nova")
        tem_turno_noturno = informacoes_ue.get("possui_turno_noturno", False)
        qtd_turmas_noturno = informacoes_ue.get("quantidade_turmas_noturno", 0)
        # ----------------------------------

        # ================= REGRAS FIXAS =================
        if sigla_tipo == "CEI":
            return 1

        if sigla_tipo == "CEMEI":
            return 2

        # ================= REGRAS DEPENDENTES DE CLASSES =================
        if qtd_classes is None:
            logger.warning(
                "Cálculo de módulo para Coordenador Pedagógico requer "
                "quantidade de classes (UE %s).",
                informacoes_ue.get("codigoUE"),
            )
            return 0  # valor seguro até integração completa

        # -------- EMEI --------
        if sigla_tipo == "EMEI":
            return 1 if qtd_classes <= 20 else 2

        # -------- EMEF / EMEBS --------
        if sigla_tipo in ("EMEF", "EMEBS"):
            if qtd_classes <= 14:
                return 1

            if 15 <= qtd_classes <= 35:
                # Regra especial: noturno com 5+ turmas
                if tem_turno_noturno and qtd_turmas_noturno >= 5:
                    return 3
                return 2

            if 36 <= qtd_classes <= 50:
                return 3

            if qtd_classes > 50:
                return 4

        return 0
