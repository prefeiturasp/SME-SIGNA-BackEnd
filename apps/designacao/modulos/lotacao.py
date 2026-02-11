import logging

logger = logging.getLogger(__name__)

class ModuloLotacaoCalculator:

    CARGO_DIRETOR = "3360"
    CARGO_SECRETARIO = "3182"
    CARGO_ASSISTENTE = "3085"

    def calcular(self, cargo: dict, informacoes_ue: dict) -> int:
        codigo_cargo = str(cargo.get("codigo_cargo"))
        sigla_tipo = (informacoes_ue.get("siglaTipoEscola") or "").strip().upper()
        qtd_classes = informacoes_ue.get("quantidade_classes")

        if codigo_cargo == self.CARGO_DIRETOR:
            return 1

        if codigo_cargo == self.CARGO_SECRETARIO:
            if sigla_tipo in ("EMEBS", "EMEF", "EMEFM", "CIEJA"):
                return 1
            else:
                return 0

        if codigo_cargo == self.CARGO_ASSISTENTE:
            if sigla_tipo == "CEI":
                return 1

            if sigla_tipo in ("CEMEI", "EMEI", "EMEBS", "EMEF", "EMEFM"):
                if qtd_classes is None:
                    logger.warning("Quantidade de classes ausente.")
                    return 0
                return 1 if qtd_classes <= 20 else 2

        return 0
