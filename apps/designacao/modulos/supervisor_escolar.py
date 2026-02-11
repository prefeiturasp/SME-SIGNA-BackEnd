import logging

logger = logging.getLogger(__name__)


class ModuloSupervisorEscolarCalculator:
    """
    Regra de cálculo de módulo para o cargo:
    - 3352 (Supervisor Escolar)

    O módulo é definido exclusivamente pela DRE da unidade escolar.
    """

    CARGO_SUPERVISOR_ESCOLAR = "3352"

    MODULOS_POR_DRE = {
        "108200": 53,  # Campo Limpo
        "109000": 42,  # Pirituba / Jaraguá
        "108600": 40,  # Ipiranga
        "109300": 40,  # São Miguel
        "108900": 38,  # Penha
        "108500": 37,  # Guaianases
        "109200": 36,  # São Mateus
        "108400": 35,  # Freguesia / Brasilândia
        "108700": 34,  # Itaquera
        "108300": 32,  # Capela do Socorro
        "109100": 31,  # Santo Amaro
        "108100": 30,  # Butantã
        "108800": 30,  # Jaçanã / Tremembé
    }

    def calcular(self, cargo: dict, informacoes_ue: dict) -> int:
        codigo_dre = informacoes_ue.get("codigoDRE")

        if not codigo_dre:
            logger.warning(
                "Código da DRE ausente ao calcular módulo de Supervisor Escolar "
                "(UE %s).",
                informacoes_ue.get("codigoUE"),
            )
            return 0

        modulo = self.MODULOS_POR_DRE.get(codigo_dre)

        if modulo is None:
            logger.warning(
                "DRE %s não possui módulo definido para Supervisor Escolar. "
                "Usando valor padrão 0.",
                codigo_dre,
            )
            return 0

        return modulo
