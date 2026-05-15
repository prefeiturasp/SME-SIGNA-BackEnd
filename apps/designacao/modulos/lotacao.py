import logging

logger = logging.getLogger(__name__)


class ModuloLotacaoCalculator:

    CARGO_DIRETOR = "3360"
    CARGO_SECRETARIO = "3182"
    CARGO_ASSISTENTE = "3085"

    def calcular(self, cargo: dict, informacoes_ue: dict) -> int:
        codigo_cargo = self._obter_codigo_cargo(cargo)
        sigla_tipo = self._obter_sigla(informacoes_ue)
        dados_turmas = informacoes_ue.get("turmas") or {}
        qtd_classes = dados_turmas.get("total")

        if codigo_cargo == self.CARGO_DIRETOR:
            return self._regra_diretor()

        if codigo_cargo == self.CARGO_SECRETARIO:
            return self._regra_secretario(sigla_tipo)

        if codigo_cargo == self.CARGO_ASSISTENTE:
            return self._regra_assistente(sigla_tipo, qtd_classes)

        return 0

    def _obter_codigo_cargo(self, cargo: dict) -> str:
        return str(cargo.get("codigo_cargo"))

    def _obter_sigla(self, informacoes_ue: dict) -> str:
        return (informacoes_ue.get("siglaTipoEscola") or "").strip().upper()

    def _regra_diretor(self) -> int:
        return 1

    def _regra_secretario(self, sigla_tipo: str) -> int:
        tipos_validos = {"EMEBS", "EMEF", "EMEFM", "CIEJA"}
        return 1 if sigla_tipo in tipos_validos else 0

    def _regra_assistente(self, sigla_tipo: str, qtd_classes: int) -> int:
        if sigla_tipo == "CEI":
            return 1

        tipos_dependentes_classes = {
            "CEMEI",
            "EMEI",
            "EMEBS",
            "EMEF",
            "EMEFM",
        }

        if sigla_tipo not in tipos_dependentes_classes:
            return 0

        if qtd_classes is None:
            logger.warning("Quantidade de classes ausente.")
            return 0

        return 1 if qtd_classes <= 20 else 2
