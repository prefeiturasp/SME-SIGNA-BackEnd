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
    def obter_informacoes_escolares(cls, codigo_ue: str) -> list:
        cargos = SmeIntegracaoService.buscar_funcionarios_escolares(
            codigo_ue
        )

        resultado = []

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
                    cargos_servidor = []

                cargo_sobreposto = None
                if cargos_servidor:
                    cargo_sobreposto = cargos_servidor[0].get(
                        "cargoSobreposto"
                    )

                resultado.append({
                    "rf": rf,
                    "nome": servidor.get("nome"),
                    "cargoSobreposto": (
                        f"{cargo_sobreposto} - v1"
                        if cargo_sobreposto else None
                    ),
                })

        return resultado
