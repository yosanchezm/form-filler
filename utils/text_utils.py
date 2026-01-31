"""
Utilidades para normalización y procesamiento de texto.
"""

import re
import unicodedata
from typing import Optional, Tuple, List

from config.settings import MIN_UNDERSCORES


def norm(s: str) -> str:
    """
    Normaliza un string para comparaciones: lowercase, sin acentos, sin puntuación.
    """
    if s is None:
        return ""
    s = str(s).replace("\n", " ").strip().lower()
    s = "".join(
        c for c in unicodedata.normalize("NFKD", s)
        if not unicodedata.combining(c)
    )
    s = re.sub(r"[^\w\s]", " ", s)
    s = re.sub(r"\s+", " ", s).strip()
    return s


def looks_empty_or_underscores(text: str) -> bool:
    """
    Verifica si un texto está vacío o solo contiene underscores y espacios.
    """
    t = (text or "").strip()
    if t == "":
        return True
    return bool(re.fullmatch(r"[_\s]+", t))


def first_underscore_span(text: str, min_underscores: int = MIN_UNDERSCORES) -> Optional[Tuple[int, int]]:
    """
    Encuentra la primera secuencia de underscores consecutivos que supere el mínimo.
    Retorna (start, end) o None.
    """
    m = re.search(r"_{%d,}" % min_underscores, text)
    return m.span() if m else None


def find_all_underscore_spans(text: str, min_underscores: int = MIN_UNDERSCORES) -> List[Tuple[int, int]]:
    """
    Encuentra TODAS las secuencias de underscores en el texto.
    
    Útil para campos como: "a los ____ días del mes de ____ de 20__"
    
    Returns:
        Lista de tuplas (start, end) para cada secuencia de underscores
    """
    spans = []
    for m in re.finditer(r"_{%d,}" % min_underscores, text):
        spans.append(m.span())
    return spans


def extract_label_before_underscores(text: str) -> str:
    """
    Extrae el texto antes de la primera secuencia de underscores.
    Útil para detectar el label de un campo.
    """
    span = first_underscore_span(text, MIN_UNDERSCORES)
    if not span:
        return ""
    start, _ = span
    label = text[:start].strip()
    label = re.sub(r"\s+", " ", label).strip()
    return label


# =====================
# Detección de Checkboxes
# =====================

# Patrones comunes de checkbox en español
CHECKBOX_PATTERNS = [
    # Sí___ No___
    r"(?P<label1>Sí|Si)\s*[_]{2,}\s*(?P<label2>No)\s*[_]{2,}",
    # ( ) Opción o [  ] Opción
    r"[\(\[]\s*[\)\]]\s*(?P<option>[^\(\[\]\)]+)",
    # Opción ___
    r"(?P<option_name>Persona\s+natural|Persona\s+jurídica|Consorcio|Unión\s+temporal|Otro)\s*[_]{2,}",
    # X___ o ___X (marca con X)
    r"(?P<pre_mark>X)?\s*[_]{3,}\s*(?P<post_mark>X)?",
]

CHECKBOX_RE = [re.compile(p, re.IGNORECASE) for p in CHECKBOX_PATTERNS]


def detect_checkbox_field(text: str) -> Optional[dict]:
    """
    Detecta si el texto contiene un campo de checkbox.
    
    Returns:
        Dict con info del checkbox o None:
        {
            "type": "yes_no" | "option" | "single",
            "options": ["Sí", "No"] | ["Opción1", "Opción2"],
            "raw": "texto original"
        }
    """
    text = text.strip()
    
    # Patrón Sí/No
    match_si_no = re.search(r"(Sí|Si)\s*[_]{2,}\s*(No)\s*[_]{2,}", text, re.IGNORECASE)
    if match_si_no:
        return {
            "type": "yes_no",
            "options": ["Sí", "No"],
            "raw": text
        }
    
    # Patrón tipo lista de opciones (Persona natural ___, Persona jurídica ___)
    options_pattern = r"(Persona\s+natural|Persona\s+jurídica\s+nacional|Persona\s+jurídica\s+extranjera|" \
                     r"Sucursal|Unión\s+temporal|Consorcio|Otro)\s*[_]{2,}"
    matches = re.findall(options_pattern, text, re.IGNORECASE)
    if matches:
        return {
            "type": "multi_option",
            "options": [m.strip() for m in matches],
            "raw": text
        }
    
    # Checkbox individual con paréntesis o corchetes
    bracket_match = re.search(r"[\(\[]\s*[\)\]]\s*(.+?)(?=[\(\[]|$)", text)
    if bracket_match:
        return {
            "type": "single",
            "options": [bracket_match.group(1).strip()],
            "raw": text
        }
    
    return None


def is_checkbox_field(text: str) -> bool:
    """Verifica si el texto parece ser un campo de checkbox."""
    return detect_checkbox_field(text) is not None


# =====================
# Detección de Texto Destacado
# =====================

HIGHLIGHTED_PATTERNS = [
    # Texto en mayúsculas sostenidas
    r"[A-ZÁÉÍÓÚÑ]{10,}",
    # Texto subrayado (simulado con formato específico)
    r"(?:nombre|razón\s+social|nit|cédula|dirección|teléfono|correo)\s+(?:del|de\s+la)?\s*(?:representante|empresa|proponente|entidad)",
]


def detect_highlighted_field(text: str) -> Optional[dict]:
    """
    Detecta campos que aparecen destacados (mayúsculas, etc).
    
    Returns:
        Dict con info del campo destacado o None
    """
    text_clean = text.strip()
    
    # Todo mayúsculas sostenidas (más de 10 chars)
    if re.match(r'^[A-ZÁÉÍÓÚÑ\s]{10,}$', text_clean):
        return {
            "type": "uppercase",
            "label": text_clean,
            "raw": text
        }
    
    # Patrones conocidos de labels de formularios
    for pattern in HIGHLIGHTED_PATTERNS[1:]:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            return {
                "type": "label_pattern",
                "label": match.group(0),
                "raw": text
            }
    
    return None


# =====================
# Detección de Fechas
# =====================

DATE_PATTERNS = [
    # "a los ____ días del mes de ____ de 20__"
    r"a\s+los\s+[_]+\s+días\s+del\s+mes\s+de\s+[_]+\s+de\s+20[_]+",
    # "Fecha: ____/____/____"
    r"[Ff]echa[:\s]+[_/]+",
    # "__ de _______ de 20__"
    r"[_]+\s+de\s+[_]+\s+de\s+20[_]+",
]


def detect_date_field(text: str) -> Optional[dict]:
    """
    Detecta si el texto contiene un campo de fecha.
    
    Returns:
        Dict con info del campo de fecha o None
    """
    for pattern in DATE_PATTERNS:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            return {
                "type": "date",
                "format_hint": pattern,
                "raw": match.group(0)
            }
    return None


def is_date_field(text: str) -> bool:
    """Verifica si el texto parece ser un campo de fecha."""
    return detect_date_field(text) is not None


# =====================
# Extracción de contexto
# =====================

def extract_field_context(text: str, max_context: int = 100) -> dict:
    """
    Extrae contexto útil de un campo para ayudar a la IA.
    
    Returns:
        Dict con label, contexto previo, contexto posterior
    """
    spans = find_all_underscore_spans(text)
    
    if not spans:
        return {"label": "", "before": "", "after": "", "num_fields": 0}
    
    first_start = spans[0][0]
    last_end = spans[-1][1]
    
    before = text[:first_start].strip()[-max_context:]
    after = text[last_end:].strip()[:max_context]
    
    return {
        "label": extract_label_before_underscores(text),
        "before": before,
        "after": after,
        "num_fields": len(spans),
        "field_positions": spans
    }

