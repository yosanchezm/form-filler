"""
Procesador principal del documento.
"""

import io
from typing import Dict, List, Any, Tuple

from docx import Document

from models.events import FillEvent
from core.filler import (
    fill_bracket_placeholders,
    fill_paragraph_underscore_fields,
    fill_table_fields,
    apply_ai_updates
)
from ai.prompts import build_prompt
from ai.providers import call_llm


def run_mvp2(
    docx_bytes: bytes,
    kb: Dict[str, Dict[str, Any]],
    use_ai: bool,
    provider: str,
    api_key: str,
    model: str,
    confidence_threshold: float,
    temperature: float
) -> Tuple[bytes, List[FillEvent], List[FillEvent], List[Dict[str, Any]]]:
    """
    Procesa un documento DOCX rellenando campos con reglas y opcionalmente con IA.
    
    Args:
        docx_bytes: Bytes del documento DOCX
        kb: Base de conocimiento con claves '__raw__' y '__norm__'
        use_ai: Si se debe usar IA para completar campos pendientes
        provider: Proveedor de IA
        api_key: Clave API del proveedor
        model: Modelo a usar
        confidence_threshold: Umbral de confianza mínimo
        temperature: Temperatura del modelo
    
    Returns:
        - docx output bytes
        - filled_by_rules: Eventos rellenados por reglas
        - filled_by_ai: Eventos rellenados por IA
        - skipped_ai_updates: Actualizaciones de IA no aplicadas
    """
    doc = Document(io.BytesIO(docx_bytes))
    kb_norm = kb["__norm__"]
    kb_raw = kb["__raw__"]

    filled_rules: List[FillEvent] = []
    ai_targets: List[Dict[str, Any]] = []

    # 1) Bracket placeholders: [ ... ]
    fr, targets_br = fill_bracket_placeholders(doc, kb_norm)
    filled_rules.extend(fr)
    ai_targets.extend(targets_br)

    # 2) Underscore fields in paragraphs
    fr, targets_u = fill_paragraph_underscore_fields(doc, kb_norm)
    filled_rules.extend(fr)
    ai_targets.extend(targets_u)

    # 3) Table fields
    fr, targets_t = fill_table_fields(doc, kb_norm)
    filled_rules.extend(fr)
    ai_targets.extend(targets_t)

    filled_ai: List[FillEvent] = []
    skipped: List[Dict[str, Any]] = []

    # 4) AI completion for remaining targets
    if use_ai and ai_targets:
        system, user = build_prompt(ai_targets, kb_raw)
        llm_out = call_llm(provider, api_key, model, system, user, temperature=temperature)

        updates = llm_out.get("updates", [])
        if not isinstance(updates, list):
            raise ValueError("La IA no devolvió 'updates' como lista.")

        applied, skipped_ai = apply_ai_updates(doc, updates, confidence_threshold)
        filled_ai.extend(applied)
        skipped.extend(skipped_ai)

    out_buf = io.BytesIO()
    doc.save(out_buf)
    return out_buf.getvalue(), filled_rules, filled_ai, skipped
