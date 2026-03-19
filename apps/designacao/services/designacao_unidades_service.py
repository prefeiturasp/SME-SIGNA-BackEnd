import logging
from datetime import datetime
from apps.usuarios.services.sme_integracao_service import SmeIntegracaoService
from apps.designacao.services.designacao_servidor_service import DesignacaoServidorService
from apps.designacao.constants.cargos_gestao_escolar import TURNOS_MAP
from apps.helpers.exceptions import SmeIntegracaoException
from apps.designacao.modulos import Calculadores
from apps.designacao.models import Designacao

logger = logging.getLogger(__name__)

class DesignacaoUnidadeService:
    """
    Orquestra dados da unidade escolar e delega
    o cálculo de módulos para os calculators específicos.
    """

    @classmethod
    def obter_informacoes_escolares(cls, codigo_ue: str) -> dict:
        cargos = SmeIntegracaoService.buscar_funcionarios_escolares(codigo_ue)
        informacoes_ue = SmeIntegracaoService.consulta_informacoes_unidades_escolares(codigo_ue)
        turmas = cls.calcular_turmas(codigo_ue)
        informacoes_ue.update({'turmas': turmas})

        for cargo_ue in cargos:
            cargo_ue["modulo"] = cls._definir_modulo_cargo(cargo_ue, informacoes_ue)

            for servidor in cargo_ue.get("servidores", []):
                cls._enriquecer_dados_servidor(servidor)

        cargos_por_codigo = {
            cargo["codigo_cargo"]: cargo
            for cargo in cargos
        }


        return {
            "cargos": Designacao.get_cargos_formatados(),
            "funcionarios_unidade": cargos_por_codigo,
            "turmas": turmas,
            "codigo_hierarquico": "Indisponível"
        }

    @classmethod
    def _definir_modulo_cargo(cls, cargo_ue: dict, informacoes_ue: dict) -> int:
        """Busca o calculador específico e retorna o valor do módulo."""
        codigo_cargo = str(cargo_ue.get("codigo_cargo"))
        calculator = Calculadores.get(codigo_cargo)

        if not calculator:
            logger.debug("Cargo %s não possui regra de módulo definida.", codigo_cargo)
            return 0
        
        return calculator.calcular(cargo_ue, informacoes_ue)

    @classmethod
    def _enriquecer_dados_servidor(cls, servidor: dict):

        rf = servidor.get("rf")

        try:
            usuario = SmeIntegracaoService.informacao_usuario_sgp(rf)

            cargos = SmeIntegracaoService.consulta_cargos_funcionario(rf)

            cargo = cargos[0] if cargos else {}

            dados_servidor = DesignacaoServidorService.montar_dados_servidor(
                usuario,
                cargo
            )

            servidor.clear()
            servidor.update(dados_servidor)

        except SmeIntegracaoException:
            logger.warning("Falha ao montar designação do servidor RF %s", rf)

            servidor.clear()
            servidor.update({
                "nome_servidor": None,
                "nome_civil": None,
                "rf": rf,
                "vinculo": None,
                "cargo_base": None,
                "lotacao": None,
                "cargo_sobreposto_funcao_atividade": None,
                "local_de_exercicio": None,
                "laudo_medico": None,
                "local_de_servico": None
            })

    @staticmethod
    def _mapear_info_cargo(info: dict) -> dict:
        """Tradução de campos camelCase (SME) para snake_case (Interno)."""
        return {
            "cargo_sobreposto": info.get("cargoSobreposto"),
            "vinculo_cargo_sobreposto": info.get("tipoVinculoCargoSobreposto"),
            "lotacao_cargo_sobreposto": info.get("ueCargoSobreposto"),
            "cargo_base": info.get("cargoBase"),
            "funcao_atividade": info.get("funcaoAtividade"),
        }
    
    @classmethod

    def calcular_turmas(cls, codigo_ue: str) -> dict:
        ano_letivo = datetime.now().year

        turmas = SmeIntegracaoService.buscar_turmas_ue_ano(
            codigo_ue,
            ano_letivo
        )

        resultado = {
            "total": 0,
            "por_turno": {
                "manhã": 0,
                "intermediário": 0,
                "tarde": 0,
                "vespertino": 0,
                "noite": 0,
                "integral": 0,
            }
        }

        for turma in turmas:
            codigo_turma = turma.get("codigoTurma")
            dados = SmeIntegracaoService.buscar_dados_turma(
                codigo_turma
            )

            tipo_turno = dados.get("tipoTurno")
            turno = TURNOS_MAP.get(tipo_turno)

            resultado["total"] += 1

            if turno:
                resultado["por_turno"][turno] += 1

        return resultado
    
    @staticmethod
    def listar_cargos_vaga():
            """Para o endpoint unidade/cargos/"""
            return Designacao.get_cargos_formatados()