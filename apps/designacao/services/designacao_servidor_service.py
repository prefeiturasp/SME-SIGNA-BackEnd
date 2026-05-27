"""Serviço de designação de servidor.

Fornece métodos para obter e montar dados de designação do servidor a partir
integrações com o SGP.
"""

import logging

from apps.helpers.exceptions import SmeIntegracaoException
from apps.usuarios.services.sme_integracao_service import SmeIntegracaoService

logger = logging.getLogger(__name__)


class DesignacaoServidorService:
    """Serviço responsável por montar a designação do servidor."""

    @classmethod
    def obter_designacao(cls, registro_funcional: str) -> dict:
        """Obtém e monta a designação do servidor.

        Args:
            registro_funcional: Registro funcional do servidor.

        Returns:
            dict: Dados padronizados da designação do servidor.

        Raises:
            SmeIntegracaoException: Se o registro funcional não for
            informado ou o servidor não tiver cargos.
        """

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
        """Monta o dicionário padronizado com dados do servidor e do cargo.

        Args:
            usuario: Dados do usuário retornados pela integração SGP.
            cargo: Dados do cargo retornados pela integração SGP.

        Returns:
            dict: Dados padronizados da designação do servidor.
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
