"""Opções e decomposição do parâmetro ``tipo`` das listagens de atos.

O parâmetro ``tipo`` é compartilhado pelas listagens de portarias, de atos
administrativos e pelo histórico de designações. Além dos tipos gravados em
``AtoAdministrativo.tipo``, as opções incluem pseudo-tipos que nunca chegam
ao banco:

* ``DESIGNACAO_CESSACAO``: união de designação e cessação.
* ``<TIPO>_<TIPO_PAI>`` (ex.: ``APOSTILA_CESSACAO``): ato do primeiro tipo
  cujo pai é do segundo. A combinação acompanha a regra de hierarquia de
  ``AtoAdministrativo.TIPOS_PAI_VALIDOS``.

Manter as opções e a decomposição em um único lugar evita que as listagens
divirjam quando um novo tipo de ato for criado.
"""

from apps.designacao.models.ato_administrativo import AtoAdministrativo

TIPO_CHOICES_SIMPLES = AtoAdministrativo.Tipo.choices + [
    ("DESIGNACAO_CESSACAO", "Designação e Cessação"),
]

TIPO_CHOICES = TIPO_CHOICES_SIMPLES + [
    ("INSUBSISTENCIA_DESIGNACAO", "Insubsistência de Designação"),
    ("INSUBSISTENCIA_CESSACAO", "Insubsistência de Cessação"),
    ("APOSTILA_DESIGNACAO", "Apostila de Designação"),
    ("APOSTILA_CESSACAO", "Apostila de Cessação"),
    ("INSUBSISTENCIA_APOSTILA", "Insubsistência de Apostila"),
    ("INSUBSISTENCIA_INSUBSISTENCIA", "Tornar sem efeito"),
]


def dividir_tipo_composto(value: str) -> tuple[str, str] | None:
    """Divide um pseudo-tipo composto em ``(tipo, tipo_do_pai)``.

    O primeiro trecho separado por ``_`` é sempre o tipo do ato e o
    restante, o tipo do pai. Usar ``partition`` em vez de ``split`` evita
    que um valor com mais de um separador quebre a decomposição.

    Args:
        value: Valor do parâmetro ``tipo``.

    Returns:
        tuple[str, str]|None: O tipo do ato e o tipo do pai, ou None
        quando o valor é um tipo simples.

    """
    tipo, separador, pai = value.partition("_")
    if not separador:
        return None
    return tipo, pai
