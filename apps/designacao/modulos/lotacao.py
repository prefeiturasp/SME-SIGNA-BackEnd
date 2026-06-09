"""Calculadora de módulo baseada na lotação do cargo escolar.

Aplica regras específicas para Diretor, Secretário e Assistente de Diretor
conforme o tipo de escola e quantidade de classes.
"""

import logging

logger = logging.getLogger(__name__)


class ModuloLotacaoCalculator:
    """Calcula o módulo de lotação para cargos de direção escolar."""

    CARGO_DIRETOR = "3360"
    CARGO_SECRETARIO = "3182"
    CARGO_ASSISTENTE = "3085"

    def calcular(self, cargo: dict, informacoes_ue: dict) -> int:
        """Calcula o módulo de lotação para o cargo fornecido.

        Args:
            cargo: Dicionário com dados do cargo.
            informacoes_ue: Dicionário com informações da unidade escolar.

        Returns:
            int: Módulo calculado com base no cargo e tipo de escola.
        """
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
        """Extrai o código do cargo do dicionário do cargo.

        Args:
            cargo: Dicionário com dados do cargo.

        Returns:
            str: Código do cargo como string.
        """
        return str(cargo.get("codigo_cargo"))

    def _obter_sigla(self, informacoes_ue: dict) -> str:
        """Retorna a sigla do tipo de escola normalizada.

        Args:
            informacoes_ue: Dicionário com informações da unidade escolar.

        Returns:
            str: Sigla do tipo de escola em maiúsculas.
        """
        return (informacoes_ue.get("siglaTipoEscola") or "").strip().upper()

    def _regra_diretor(self) -> int:
        """Retorna o módulo fixo para o cargo de Diretor."""
        return 1

    def _regra_secretario(self, sigla_tipo: str) -> int:
        """Calcula o módulo do secretário de acordo com o tipo de escola.

        Args:
            sigla_tipo: Sigla do tipo de escola.

        Returns:
            int: 1 para tipos válidos, 0 caso contrário.
        """
        tipos_validos = {"EMEBS", "EMEF", "EMEFM", "CIEJA"}
        return 1 if sigla_tipo in tipos_validos else 0

    def _regra_assistente(
        self,
        sigla_tipo: str,
        qtd_classes: int | None,
    ) -> int:
        """Calcula o módulo do assistente de direção conforme o tipo e classes.

        Args:
            sigla_tipo: Sigla do tipo de escola.
            qtd_classes: Quantidade de classes da unidade.

        Returns:
            int: Módulo calculado para assistente de direção.
        """
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
