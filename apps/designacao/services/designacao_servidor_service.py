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

        usuario = SmeIntegracaoService.informacao_usuario_sgp(registro_funcional)

        cargos = SmeIntegracaoService.consulta_cargos_funcionario(registro_funcional)

        if not cargos:
            raise SmeIntegracaoException("Servidor não possui cargos")

        cargo = cargos[0]

        return cls.montar_dados_servidor(usuario, cargo)

    @classmethod
    def montar_dados_servidor(cls, usuario: dict, cargo: dict) -> dict:
        """
        Monta o dicionário padronizado de designação do servidor.
        """

        possui_cargo_sobreposto = bool(cargo.get("cargoSobreposto"))

        cargo_sobreposto_funcao_atividade = (
            cargo.get("cargoSobreposto")
            if possui_cargo_sobreposto
            else cargo.get("funcaoAtividade")
        )

        cd_cargo_sobreposto_funcao_atividade = (
            cargo.get("cdCargoSobreposto")
            if possui_cargo_sobreposto
            else cargo.get("cdUeFuncaoAtividade")
        )

        local_exercicio = (
            cargo.get("ueCargoSobreposto")
            if possui_cargo_sobreposto
            else cargo.get("ueFuncaoAtividade")
        )

        return {
            "nome_servidor": usuario.get("nome"),
            "nome_civil": "",  # to-do: ajustar quando tiver api eol que traga valor
            "rf": usuario.get("codigoRf"),
            "vinculo": cargo.get("tipoVinculoCargoBase"),
            "cd_cargo_base": cargo.get("cdCargoBase"),
            "cargo_base": cargo.get("cargoBase"),
            "lotacao": cargo.get("ueCargoBase"),
            "cd_cargo_sobreposto_funcao_atividade": cd_cargo_sobreposto_funcao_atividade,  # noqa: E501
            "cargo_sobreposto_funcao_atividade": cargo_sobreposto_funcao_atividade,
            "local_de_exercicio": local_exercicio,
            "laudo_medico": "Indisponível",
            "local_de_servico": "Indisponível",
        }
