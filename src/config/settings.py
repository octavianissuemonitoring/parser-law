"""
Configurație pentru parserul de acte legislative
"""

# Tipuri de acte normative recunoscute
TIPURI_ACTE_NORMATIVE = [
    'LEGE',
    'ORDONANȚĂ DE URGENȚĂ',
    'ORDONANȚĂ',
    'HOTĂRÂRE',
    'DECRET',
    'ORDIN',
    'REGULAMENT',
    'NORMĂ',
    'INSTRUCȚIUNE',
    'METODOLOGIE'
]

# Praguri validare
MIN_ARTICLE_TEXT_LENGTH = 10
MAX_YEAR = 2100
MIN_YEAR = 1900

# Weights pentru confidence score
CONFIDENCE_WEIGHTS = {
    'has_articles': 0.5,
    'has_structure': 0.2,
    'has_content': 0.2,
    'has_metadata': 0.1
}

# Timeouts și delays
REQUEST_TIMEOUT = 30
INTER_REQUEST_DELAY = 2.0
