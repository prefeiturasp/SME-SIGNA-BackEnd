import logging

from apps.usuarios.services.sme_integracao_service import (
    SmeIntegracaoService
)
from apps.helpers.exceptions import SmeIntegracaoException

logger = logging.getLogger(__name__)


class DesignacaoUnidadeService:
    """
    Orquestra dados da unidade.
    """

    @classmethod
    def obter_informacoes_escolares(cls, codigo_ue: str) -> dict:
        cargos = (
            SmeIntegracaoService.buscar_funcionarios_escolares(
                codigo_ue
            )
        )

        for cargo in cargos:
            servidores = cargo.get("servidores", [])

            for servidor in servidores:
                rf = servidor.get("rf")

                try:
                    cargos_servidor = (
                        SmeIntegracaoService
                        .consulta_cargos_funcionario(rf)
                    )
                except SmeIntegracaoException:
                    logger.warning(
                        "Falha ao consultar cargos do servidor RF %s",
                        rf
                    )
                    servidor["cargoSobreposto"] = None
                    continue

                cargo_sobreposto = None
                if cargos_servidor:
                    cargo_sobreposto = cargos_servidor[0].get(
                        "cargoSobreposto"
                    )

                servidor["cargoSobreposto"] = cargo_sobreposto

        cargos_por_codigo = {
            cargo["codigo_cargo"]: cargo
            for cargo in cargos
        }

        return {
            "funcionarios_unidade": cargos_por_codigo
        }