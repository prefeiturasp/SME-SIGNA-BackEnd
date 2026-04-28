import logging
from datetime import datetime
from typing import Dict, Any

from apps.usuarios.services.sme_integracao_service import SmeIntegracaoService
from apps.designacao.services.designacao_servidor_service import DesignacaoServidorService
from apps.designacao.constants.cargos_gestao_escolar import TURNOS_MAP
from apps.helpers.exceptions import SmeIntegracaoException
from apps.designacao.modulos import Calculadores
from apps.designacao.models import Designacao
from apps.unidades.services.unidades_service import UnidadeIntegracaoService

import re
import unicodedata

logger = logging.getLogger(__name__)


def normalizar(texto: str) -> str:
    if not texto:
        return ""
    texto = texto.lower()
    texto = unicodedata.normalize("NFD", texto)
    texto = texto.encode("ascii", "ignore").decode("utf-8")
    return texto


class CicloService:
    CICLOS_MAPEADOS = {
        "alfabetizacao": "cicloAlfabetizacao",
        "interdisciplinar": "cicloInterdisciplinar",
        "autoral": "cicloAutoral",
        "basica": "cicloBasicoEja",
        "complementar": "cicloComplementarEja",
        "final": "cicloFinalEja",
        "bercario_i": "cicloBercarioI",
        "bercario_ii": "cicloBercarioII",
        "mini_grupo_i": "cicloMiniGrupoI",
        "mini_grupo_ii": "cicloMiniGrupoII",
        "infantil": "cicloInfantil",
        "sem_ciclo": "semCiclo",
    }

    @staticmethod
    def extrair_numero(nome: str) -> int | None:
        match = re.search(r"\d+", nome or "")
        return int(match.group()) if match else None

    @classmethod
    def definir_ciclo_turma(cls, turma: Dict[str, Any]) -> str:
        modalidade = turma.get("siglaModalidade")
        nome = turma.get("nomeTurmaEOL", "")

        if modalidade == "EF":
            return cls._ciclo_ef(nome)

        if modalidade == "EJA":
            return cls._ciclo_eja(nome)

        if modalidade == "EM":
            return cls._ciclo_em(nome)

        if modalidade == "EI":
            return cls._ciclo_ei(nome)

        return "sem_ciclo"

    @classmethod
    def _ciclo_ef(cls, nome: str) -> str:
        ano = cls.extrair_numero(nome)
        if not ano:
            return "sem_ciclo"

        if 1 <= ano <= 3:
            return "alfabetizacao"
        if 4 <= ano <= 6:
            return "interdisciplinar"
        if 7 <= ano <= 9:
            return "autoral"

        return "sem_ciclo"

    @classmethod
    def _ciclo_eja(cls, nome: str) -> str:
        semestre = cls.extrair_numero(nome)

        mapa = {
            1: "alfabetizacao",
            2: "basica",
            3: "complementar",
            4: "final",
        }

        return mapa.get(semestre, "sem_ciclo")

    @classmethod
    def _ciclo_em(cls, nome: str) -> str:
        serie = cls.extrair_numero(nome)
        if not serie:
            return "sem_ciclo"

        return f"{serie}_serie"

    @staticmethod
    def _ciclo_ei(nome: str) -> str:
        nome_norm = normalizar(nome)

        if re.search(r"\bbercario\s*ii\b", nome_norm):
            return "bercario_ii"

        if re.search(r"\bbercario\s*i\b", nome_norm):
            return "bercario_i"

        if re.search(r"\bmini\s*grupo\s*ii\b", nome_norm):
            return "mini_grupo_ii"

        if re.search(r"\bmini\s*grupo\s*i\b", nome_norm):
            return "mini_grupo_i"

        if re.search(r"\binfantil\b", nome_norm):
            return "infantil"

        return "sem_ciclo"

    @classmethod
    def mapear_nome_ciclo(cls, ciclo: str) -> str:
        return cls.CICLOS_MAPEADOS.get(ciclo, "semCiclo")

    @classmethod
    def listar_ciclos_saida(cls) -> list[str]:
        return list(set(cls.CICLOS_MAPEADOS.values()))


class TurmaService:
    @staticmethod
    def estrutura_turnos() -> Dict[str, Dict[str, Any]]:
        ciclos = CicloService.listar_ciclos_saida()
        base = dict.fromkeys(ciclos, 0)

        return {
            k: {"turno": v, "total": 0, **base}
            for k, v in {
                "manhã": "Manhã",
                "intermediário": "Intermediário",
                "tarde": "Tarde",
                "vespertino": "Vespertino",
                "noite": "Noite",
                "integral": "Integral",
            }.items()
        }

    @classmethod
    def calcular_turmas(cls, codigo_ue: str) -> Dict[str, Any]:
        ano = datetime.now().year
        turmas = SmeIntegracaoService.buscar_turmas_ue_ano(codigo_ue, ano)
        turnos = cls.estrutura_turnos()
        spi = {
            "tipo": "",
            "total": 0,
            "turnos": [
                {
                    "turno": "SPI",
                    "cicloAlfabetizacao": 0,
                    "cicloInterdisciplinar": 0,
                    "cicloAutoral": 0,
                    "semCiclo": 0,
                    "total": 0,
                }
            ]
        }

        for turma in turmas:
            codigo = turma.get("codigoTurma")

            disciplinas = SmeIntegracaoService.buscar_disciplinas_turma(codigo)

            tem_spi = cls.turma_tem_spi(disciplinas)

            if tem_spi:
                spi["tipo"] = "São Paulo Integral"

                ciclo = CicloService.definir_ciclo_turma(turma)
                ciclo_key = CicloService.mapear_nome_ciclo(ciclo)

                spi_turno = spi["turnos"][0]

                spi_turno["total"] += 1
                spi["total"] += 1

                if ciclo_key not in spi_turno:
                    spi_turno[ciclo_key] = 0

                spi_turno[ciclo_key] += 1

            dados = SmeIntegracaoService.buscar_dados_turma(codigo)

            turno_key = TURNOS_MAP.get(dados.get("tipoTurno"))
            if not turno_key:
                continue

            ciclo = CicloService.definir_ciclo_turma(turma)
            ciclo_key = CicloService.mapear_nome_ciclo(ciclo)

            turno = turnos[turno_key]
            turno["total"] += 1

            if ciclo_key not in turno:
                logger.warning("Ciclo não mapeado: %s", ciclo_key)
                turno[ciclo_key] = 0

            turno[ciclo_key] += 1

        return {
            "total": sum(t["total"] for t in turnos.values()),
            "turnos": list(turnos.values()),
            "spi": spi
        }
    
    @staticmethod
    def turma_tem_spi(disciplinas: list[Dict[str, Any]]) -> bool:
        for d in disciplinas:
            nome = d.get("disciplina", "")
            if "SP INTEGRAL" in nome.upper():
                return True
        return False


class ServidorService:
    @staticmethod
    def enriquecer(servidor: Dict[str, Any]) -> Dict[str, Any]:
        rf = servidor.get("rf")

        try:
            usuario = SmeIntegracaoService.informacao_usuario_sgp(rf)
            cargos = SmeIntegracaoService.consulta_cargos_funcionario(rf)
            cargo = cargos[0] if cargos else {}

            return DesignacaoServidorService.montar_dados_servidor(usuario, cargo)

        except SmeIntegracaoException:
            logger.warning("Falha ao montar designação do servidor RF %s", rf)
            return {
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
            }


class ModuloService:
    @staticmethod
    def definir_modulo(cargo_ue: Dict[str, Any], info_ue: Dict[str, Any]) -> int:
        codigo = str(cargo_ue.get("codigo_cargo"))
        calculator = Calculadores.get(codigo)

        if not calculator:
            logger.debug("Cargo %s sem regra de módulo", codigo)
            return 0

        return calculator.calcular(cargo_ue, info_ue)


class DesignacaoUnidadeService:
    @classmethod
    def obter_informacoes_escolares(cls, codigo_ue: str) -> Dict[str, Any]:
        cargos = SmeIntegracaoService.buscar_funcionarios_escolares(codigo_ue)
        info_ue = SmeIntegracaoService.consulta_informacoes_unidades_escolares(codigo_ue)

        codigo_dre = info_ue.get("codigoDRE")
        unidades = UnidadeIntegracaoService.get_unidades_codigo_integracao_by_dre(codigo_dre)

        unidade = next((u for u in unidades if u.get("codigoUe") == codigo_ue), None)

        turmas = TurmaService.calcular_turmas(codigo_ue)
        info_ue["turmas"] = turmas

        for cargo in cargos:
            cargo["modulo"] = ModuloService.definir_modulo(cargo, info_ue)
            cargo["servidores"] = [
                ServidorService.enriquecer(s) for s in cargo.get("servidores", [])
            ]

        return {
            "cargos": Designacao.get_cargos_formatados(),
            "funcionarios_unidade": {c["codigo_cargo"]: c for c in cargos},
            "turmas": turmas,
            "codigo_hierarquico": unidade.get("codigoIntegracao") if unidade else None,
            "spi": turmas.get("spi"),
        }

    @staticmethod
    def listar_cargos_vaga():
        return Designacao.get_cargos_formatados()
