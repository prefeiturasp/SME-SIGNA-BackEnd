import logging

from apps.usuarios.services.sme_integracao_service import (
    SmeIntegracaoService
)
from apps.designacao.constants.cargos_gestao_escolar import (
    CARGOS_GESTAO_ESCOLAR
)

from apps.usuarios.services.sme_integracao_service import SmeIntegracaoService
from apps.helpers.exceptions import SmeIntegracaoException
from apps.designacao.modulos import Calculadores

logger = logging.getLogger(__name__)


class DesignacaoUnidadeService:
    """
    Orquestra dados da unidade escolar e delega
    o cálculo de módulos para os calculators específicos.
    """

    @classmethod
    def obter_informacoes_escolares(cls, codigo_ue: str) -> dict:
        cargos = SmeIntegracaoService.buscar_funcionarios_escolares(
            codigo_ue
        )

        informacoes_ue = (
            SmeIntegracaoService
            .consulta_informacoes_unidades_escolares(codigo_ue)
        )

        for cargo_ue in cargos:
            servidores = cargo_ue.get("servidores", [])
            codigo_cargo = str(cargo_ue.get("codigo_cargo"))

            calculator = Calculadores.get(codigo_cargo)

            if not calculator:
                logger.debug(
                    "Cargo %s não possui regra de módulo definida.",
                    codigo_cargo,
                )
                cargo_ue["modulo"] = 0
            else:
                cargo_ue["modulo"] = calculator.calcular(
                    cargo_ue, informacoes_ue
                )

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
                        rf,
                    )
                    servidor.update({
                        "cargo_sobreposto": None,
                        "vinculo_cargo_sobreposto": None,
                        "lotacao_cargo_sobreposto": None,
                        "cargo_base": None,
                        "funcao_atividade": None,
                    })
                    continue

                if cargos_servidor:
                    info_cargo = cargos_servidor[0]
                    
                    servidor.update({
                        "cargo_sobreposto": info_cargo.get("cargoSobreposto"),
                        "vinculo_cargo_sobreposto": info_cargo.get("tipoVinculoCargoSobreposto"),
                        "lotacao_cargo_sobreposto": info_cargo.get("ueCargoSobreposto"),
                        "cargo_base": info_cargo.get("cargoBase"),
                        "funcao_atividade": info_cargo.get("funcaoAtividade"),
                    })
                else:
                    servidor.update({
                        "cargo_sobreposto": None,
                        "vinculo_cargo_sobreposto": None,
                        "lotacao_cargo_sobreposto": None,
                        "cargo_base": None,
                        "funcao_atividade": None,
                    })

        cargos_por_codigo = {
            cargo["codigo_cargo"]: cargo
            for cargo in cargos
        }

        return {
            "cargos": CARGOS_GESTAO_ESCOLAR,
            "funcionarios_unidade": cargos_por_codigo,
        }
