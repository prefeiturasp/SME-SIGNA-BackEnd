from apps.designacao.models.apostila import Apostila
from apps.designacao.models.apostila_detalhe import ApostilaAlteracao, ApostilaDetalhe
from apps.designacao.models.ato_administrativo import AtoAdministrativo
from apps.designacao.models.cessacao import Cessacao
from apps.designacao.models.cessacao_detalhe import CessacaoDetalhe
from apps.designacao.models.designacao import Designacao, ImpedimentoSubstituicao
from apps.designacao.models.designacao_detalhe import DesignacaoDetalhe
from apps.designacao.models.insubsistencia import Insubsistencia, TipoInsubsistencia
from apps.designacao.models.insubsistencia_detalhe import InsubsistenciaDetalhe

__all__ = [
    "Apostila",
    "ApostilaDetalhe",
    "ApostilaAlteracao",
    "AtoAdministrativo",
    "Cessacao",
    "CessacaoDetalhe",
    "Designacao",
    "ImpedimentoSubstituicao",
    "DesignacaoDetalhe",
    "Insubsistencia",
    "TipoInsubsistencia",
    "InsubsistenciaDetalhe",
]
