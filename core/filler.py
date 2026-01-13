"""
Lógica de relleno de formularios DOCX.
"""

from typing import Dict, List, Any, Tuple

from docx import Document

from config.settings import MIN_UNDERSCORES
from models.events import FillEvent
from utils.docx_utils import (
    extract_bracket_tokens_from_doc,
    iter_all_paragraphs,
    replace_in_paragraph_all,
    fill_underscore_in_paragraph,
    set_paragraph_text
)
from utils.text_utils import first_underscore_span, extract_label_before_underscores, looks_empty_or_underscores
from core.knowledge_base import find_value_for_label


def fill_bracket_placeholders(doc: Document, kb_norm: Dict[str, str]) -> Tuple[List[FillEvent], List[Dict[str, Any]]]:
    """
    Detecta tokens [....] y trata de mapearlos a KB.
    
    Returns:
        - filled events (rellenos por reglas)
        - targets para IA (si no se pudo resolver por reglas)
    """
    tokens = extract_bracket_tokens_from_doc(doc)
    filled: List[FillEvent] = []
    ai_targets: List[Dict[str, Any]] = []

    for tok in tokens:
        # intentamos mapear el contenido dentro del corchete como label
        inner = tok[1:-1].strip()
        val = find_value_for_label(inner, kb_norm)

        if val is not None:
            # aplicamos reemplazo global de tok -> val
            replaced_any = False
            for where, p in iter_all_paragraphs(doc):
                if replace_in_paragraph_all(p, {tok: str(val)}):
                    replaced_any = True
            if replaced_any:
                filled.append(FillEvent(where="doc", label=tok, value=str(val), source="rules", confidence=1.0))
        else:
            # lo mandamos a IA como target
            ai_targets.append({
                "kind": "bracket",
                "token": tok,
                "label": inner
            })

    return filled, ai_targets


def fill_paragraph_underscore_fields(doc: Document, kb_norm: Dict[str, str]) -> Tuple[List[FillEvent], List[Dict[str, Any]]]:
    """
    Rellena campos con underscores en párrafos del documento.
    
    Returns:
        - filled events
        - targets para IA
    """
    filled: List[FillEvent] = []
    ai_targets: List[Dict[str, Any]] = []

    for i, p in enumerate(doc.paragraphs):
        full = "".join(r.text for r in p.runs)
        if not full:
            continue
        if first_underscore_span(full, MIN_UNDERSCORES):
            label = extract_label_before_underscores(full)
            val = find_value_for_label(label, kb_norm)
            if val is None:
                ai_targets.append({
                    "kind": "underscore",
                    "where": f"paragraph:{i}",
                    "label": label,
                    "sample": full[:300]
                })
                continue
            if fill_underscore_in_paragraph(p, val, MIN_UNDERSCORES):
                filled.append(FillEvent(where=f"paragraph:{i}", label=label, value=str(val), source="rules", confidence=1.0))
    return filled, ai_targets


def fill_table_fields(doc: Document, kb_norm: Dict[str, str]) -> Tuple[List[FillEvent], List[Dict[str, Any]]]:
    """
    Rellena campos en tablas del documento.
    
    Returns:
        - filled events
        - targets para IA
    """
    filled: List[FillEvent] = []
    ai_targets: List[Dict[str, Any]] = []

    for ti, table in enumerate(doc.tables):
        for ri, row in enumerate(table.rows):
            cells = row.cells
            if len(cells) < 2:
                continue

            label_text = (cells[0].text or "").strip()
            value_text = (cells[1].text or "").strip()

            if not label_text:
                continue

            # Caso típico: label en col 0, valor en col 1
            if looks_empty_or_underscores(value_text):
                val = find_value_for_label(label_text, kb_norm)
                if val is None:
                    ai_targets.append({
                        "kind": "table_cell",
                        "where": f"table:{ti} row:{ri} col:1",
                        "label": label_text,
                        "sample": (cells[0].text or "")[:200]
                    })
                    continue

                if not cells[1].paragraphs:
                    cells[1].add_paragraph(str(val))
                else:
                    set_paragraph_text(cells[1].paragraphs[0], str(val))
                filled.append(FillEvent(where=f"table:{ti} row:{ri} col:1", label=label_text, value=str(val), source="rules", confidence=1.0))
            else:
                # Si el valor está dentro de un párrafo con underscores
                for pi, p in enumerate(cells[1].paragraphs):
                    full = "".join(r.text for r in p.runs)
                    if first_underscore_span(full, MIN_UNDERSCORES):
                        val = find_value_for_label(label_text, kb_norm)
                        if val is None:
                            ai_targets.append({
                                "kind": "table_cell_underscore",
                                "where": f"table:{ti} row:{ri} col:1 p:{pi}",
                                "label": label_text,
                                "sample": full[:300]
                            })
                            break
                        if fill_underscore_in_paragraph(p, val, MIN_UNDERSCORES):
                            filled.append(FillEvent(where=f"table:{ti} row:{ri} col:1 p:{pi}", label=label_text, value=str(val), source="rules", confidence=1.0))
                        break

    return filled, ai_targets


def apply_ai_updates(doc: Document, updates: List[Dict[str, Any]], confidence_threshold: float) -> Tuple[List[FillEvent], List[Dict[str, Any]]]:
    """
    Aplica las actualizaciones sugeridas por IA al documento.
    
    Args:
        doc: Documento DOCX
        updates: Lista de actualizaciones de la IA con kind, token/where/label, value, confidence
        confidence_threshold: Umbral mínimo de confianza para aplicar
    
    Returns:
        - applied events
        - skipped updates (no aplicados)
    """
    applied: List[FillEvent] = []
    skipped: List[Dict[str, Any]] = []

    for upd in updates:
        conf = float(upd.get("confidence", 0))
        if conf < confidence_threshold:
            skipped.append({**upd, "reason": f"confidence<{confidence_threshold}"})
            continue

        kind = upd.get("kind")
        value = upd.get("value")
        if value is None:
            skipped.append({**upd, "reason": "value is null"})
            continue

        if kind == "bracket":
            token = upd.get("token")
            if not token:
                skipped.append({**upd, "reason": "missing token"})
                continue
            replaced_any = False
            for where, p in iter_all_paragraphs(doc):
                if replace_in_paragraph_all(p, {token: str(value)}):
                    replaced_any = True
            if replaced_any:
                applied.append(FillEvent(where="doc", label=token, value=str(value), source="ai", confidence=conf))
            else:
                skipped.append({**upd, "reason": "token not found in doc at apply time"})
        elif kind in ("underscore", "table_cell_underscore"):
            where = upd.get("where")
            # aplicar buscando el párrafo exacto por índice no es robusto; MVP: buscamos el primer párrafo que contenga label y underscores.
            label = (upd.get("label") or "").strip()
            found = False
            for w, p in iter_all_paragraphs(doc):
                full = "".join(r.text for r in p.runs) if p.runs else (p.text or "")
                if label and label in full and first_underscore_span(full, MIN_UNDERSCORES):
                    if fill_underscore_in_paragraph(p, str(value), MIN_UNDERSCORES):
                        applied.append(FillEvent(where=w, label=label, value=str(value), source="ai", confidence=conf))
                        found = True
                        break
            if not found:
                skipped.append({**upd, "reason": "could not locate underscore field to apply"})
        elif kind == "table_cell":
            # MVP: intentar escribir en celda vacía cuyo label coincida exactamente con label
            label = (upd.get("label") or "").strip()
            found = False
            for ti, table in enumerate(doc.tables):
                for ri, row in enumerate(table.rows):
                    if len(row.cells) < 2:
                        continue
                    if (row.cells[0].text or "").strip() == label:
                        set_paragraph_text(row.cells[1].paragraphs[0], str(value)) if row.cells[1].paragraphs else row.cells[1].add_paragraph(str(value))
                        applied.append(FillEvent(where=f"table:{ti} row:{ri} col:1", label=label, value=str(value), source="ai", confidence=conf))
                        found = True
                        break
                if found:
                    break
            if not found:
                skipped.append({**upd, "reason": "could not locate table label to apply"})
        else:
            skipped.append({**upd, "reason": f"unknown kind '{kind}'"})

    return applied, skipped
