import logging

from apps.usuarios.services.sme_integracao_service import SmeIntegracaoService
from apps.helpers.exceptions import SmeIntegracaoException

logger = logging.getLogger(__name__)


class DesignacaoServidorService:
    """
    Serviço responsável por montar a designação do servidor
    (dados pessoais + cargos)
    """

    @classmethod
    def obter_designacao(cls, registro_funcional: str) -> dict:
        if not registro_funcional:
            raise SmeIntegracaoException("Registro funcional é obrigatório")

        logger.info(
            "Montando designação do servidor. RF: %s",
            registro_funcional
        )

        usuario = SmeIntegracaoService.informacao_usuario_sgp(
            registro_funcional
        )

        cargos = SmeIntegracaoService.consulta_cargos_funcionario(
            registro_funcional
        )

        if not cargos:
            raise SmeIntegracaoException("Servidor não possui cargos")

        cargo = cargos[0]

        return {
            "nome": usuario.get("nome"),
            "rf": usuario.get("codigoRf"),

            "vinculo_cargo_sobreposto": cargo.get(
                "tipoVinculoCargoSobreposto"
            ),

            "lotacao_cargo_sobreposto": cargo.get(
                "ueCargoSobreposto"
            ),

            "cargo_base": cargo.get(
                "cargoBase"
            ),
            "cargo_sobreposto": cargo.get(
                "cargoSobreposto"
            ),
            "funcao_atividade": cargo.get(
                "funcaoAtividade"
            )
        }
