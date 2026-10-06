"""Constantes de cargos da gestão escolar."""

CARGOS_GESTAO_ESCOLAR = [
    {"codigoCargo": 3085, "nomeCargo": "ASSISTENTE DE DIRETOR DE ESCOLA"},
    {"codigoCargo": 3360, "nomeCargo": "DIRETOR DE ESCOLA"},
    {"codigoCargo": 3379, "nomeCargo": "COORDENADOR PEDAGOGICO"},
    {"codigoCargo": 3182, "nomeCargo": "SECRETARIO DE ESCOLA"},
    {"codigoCargo": 3352, "nomeCargo": "SUPERVISOR ESCOLAR"},
]

TURNOS_MAP = {
    1: "manhã",
    2: "intermediário",
    3: "tarde",
    4: "vespertino",
    5: "noite",
    6: "integral",
}

# Códigos EOL de cargos de professor, usados nas regras de substituição do
# Diretor (ex.: exigência de mesma unidade escolar).
CODIGOS_CARGO_PROFESSOR = frozenset(
    {
        # Educação Infantil e Ensino Fundamental I
        3212,
        3213,
        3239,
        3875,
        # Ensino Fundamental II e Médio
        3255,
        3263,
        3271,
        3280,
        3298,
        3301,
        3336,
        3344,
        3760,
        3808,
        3816,
        3840,
        3859,
        3867,
        3868,
        3869,
        3870,
        3871,
        3873,
        3874,
        3876,
        3877,
        3878,
        3879,
        3880,
        3881,
        3882,
        3883,
        # Adjuntos
        3395,
        3409,
        3425,
        3433,
        3441,
        3450,
        3468,
        # Substitutos
        3220,
        3247,
        # Nomenclatura antiga (1º e 2º grau)
        3131,
        3310,
    }
)
