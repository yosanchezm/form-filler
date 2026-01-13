"""
Utilidades para normalización y procesamiento de texto.
"""

import re
import unicodedata
from typing import Optional, Tuple

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
