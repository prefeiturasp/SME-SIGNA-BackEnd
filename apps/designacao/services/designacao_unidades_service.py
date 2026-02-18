import logging
from datetime import datetime
from apps.usuarios.services.sme_integracao_service import SmeIntegracaoService
from apps.designacao.constants.cargos_gestao_escolar import CARGOS_GESTAO_ESCOLAR, TURNOS_MAP
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
        cargos = SmeIntegracaoService.buscar_funcionarios_escolares(codigo_ue)
        informacoes_ue = SmeIntegracaoService.consulta_informacoes_unidades_escolares(codigo_ue)
        turmas = cls.calcular_turmas(codigo_ue)
        informacoes_ue.update({'turmas': turmas})
        print("informacoes_ue", informacoes_ue)

        for cargo_ue in cargos:
            cargo_ue["modulo"] = cls._definir_modulo_cargo(cargo_ue, informacoes_ue)

            for servidor in cargo_ue.get("servidores", []):
                cls._enriquecer_dados_servidor(servidor)

        cargos_por_codigo = {
            cargo["codigo_cargo"]: cargo
            for cargo in cargos
        }


        return {
            "cargos": CARGOS_GESTAO_ESCOLAR,
            "funcionarios_unidade": cargos_por_codigo,
            "turmas": turmas,
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
        """Busca cargos externos e normaliza os dados no dicionário do servidor."""
        rf = servidor.get("rf")
        try:
            cargos_externos = SmeIntegracaoService.consulta_cargos_funcionario(rf)
            info_cargo = cargos_externos[0] if cargos_externos else {}
        except SmeIntegracaoException:
            logger.warning("Falha ao consultar cargos do servidor RF %s", rf)
            info_cargo = {}

        servidor.update(cls._mapear_info_cargo(info_cargo))

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