"""
Utilidades para manipulación de documentos DOCX.
"""

import re
from typing import Dict, List, Optional

from docx import Document

from config.settings import MIN_UNDERSCORES
from .text_utils import first_underscore_span


# =========================
# Detección de tokens
# =========================
BRACKET_RE = re.compile(r"\[[^\]]+\]")


def extract_bracket_tokens_from_doc(doc: Document) -> List[str]:
    """
    Extrae todos los tokens tipo [....] del documento.
    """
    tokens = set()
    for _, p in iter_all_paragraphs(doc):
        txt = "".join(r.text for r in p.runs) if p.runs else (p.text or "")
        for m in BRACKET_RE.finditer(txt):
            tokens.add(m.group(0))
    return sorted(tokens)


# =========================
# Manipulación de párrafos
# =========================
def set_paragraph_text(paragraph, new_text: str) -> None:
    """
    Establece el texto de un párrafo, preservando el primer run.
    """
    if not paragraph.runs:
        paragraph.add_run(new_text)
        return
    paragraph.runs[0].text = new_text
    for r in paragraph.runs[1:]:
        r.text = ""


def replace_in_paragraph_all(paragraph, replacements: Dict[str, str]) -> bool:
    """
    Reemplaza múltiples tokens dentro de un párrafo (incluye placeholders [..]).
    Maneja tokens partidos entre runs escribiendo el texto completo en el primer run.
    
    Retorna True si se hizo algún reemplazo.
    """
    if not paragraph.runs:
        return False
    full = "".join(r.text for r in paragraph.runs)
    new = full
    for k, v in replacements.items():
        if v is None:
            continue
        new = new.replace(k, str(v))
    if new != full:
        set_paragraph_text(paragraph, new)
        return True
    return False


def fill_underscore_in_paragraph(paragraph, value: str, min_underscores: int = MIN_UNDERSCORES) -> bool:
    """
    Rellena la primera secuencia de underscores con el valor proporcionado.
    
    Retorna True si se hizo el reemplazo.
    """
    full = "".join(r.text for r in paragraph.runs)
    span = first_underscore_span(full, min_underscores)
    if not span:
        return False
    start, end = span
    line_len = end - start

    v = (str(value) if value is not None else "").strip()
    v_padded = v + (" " * max(0, line_len - len(v)))  # relleno visual

    new = full[:start] + v_padded + full[end:]
    set_paragraph_text(paragraph, new)
    return True


# =========================
# Iteración de párrafos
# =========================
def iter_all_paragraphs(doc: Document):
    """
    Itera todos los párrafos del documento, incluyendo los de tablas.
    
    Yields: (identificador, paragraph)
    """
    for p in doc.paragraphs:
        yield ("paragraph", p)

    for ti, t in enumerate(doc.tables):
        for ri, row in enumerate(t.rows):
            for ci, cell in enumerate(row.cells):
                for pi, p in enumerate(cell.paragraphs):
                    yield (f"table:{ti} r:{ri} c:{ci} p:{pi}", p)
