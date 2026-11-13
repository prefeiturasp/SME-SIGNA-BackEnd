"""Mapeamento de códigos de DREs para unidades de supervisão escolar."""

SUPERVISAO_ESCOLAR_DRES_MAP = {
    "109100": 109102,
    "108700": 108702,
    "108500": 108502,
    "109200": 109202,
    "108200": 108202,
    "108400": 108402,
    "109000": 109002,
    "108100": 108102,
    "109300": 109302,
    "108300": 108302,
    "108900": 108902,
    "108800": 108802,
    "108600": 108602,
}

# Valor do parâmetro ``contexto`` que restringe DREs e UEs ao que pode ser
# usado na designação.
CONTEXTO_DESIGNACAO = "designacao"

# Siglas de tipo de unidade (``siglaTipoEscola`` do EOL) exibidas na
# designação, definidas pelo PO. As unidades desses tipos sem código da
# Estrutura Hierárquica continuam aparecendo, mas a designação é bloqueada.
TIPOS_UE_DESIGNACAO = frozenset(
    {
        "EMEF",
        "EMEI",
        "CEI DIRET",
        "CEU EMEF",
        "CEU EMEI",
        "CEU CEI",
        "CEMEI",
        "CIEJA",
        "CEU CEMEI",
        "EMEFM",
        "EMEBS",
        "CECI",
        "MOVA",
        "CEU AT COMPL",
        "CEU POLO",
        "PBA",
        "CEU POLO UAB",
        "CMCT",
        "EMFORPEF",
    }
)
