"""
Prompts para interacción con modelos de IA.
"""

import json
from typing import Dict, List, Any, Tuple


def build_prompt(targets: List[Dict[str, Any]], kb_raw: Dict[str, Any]) -> Tuple[str, str]:
    """
    Construye el prompt (system, user) para pedirle al modelo un JSON de updates.
    
    Args:
        targets: Lista de campos pendientes de llenar
        kb_raw: Base de conocimiento sin normalizar
    
    Returns:
        (system_message, user_message)
    """
    system = (
        "Eres un asistente experto en completar formularios. "
        "Debes devolver SOLO JSON válido (sin markdown, sin texto extra, sin explicaciones). "
        "No inventes valores: usa únicamente la base de conocimiento. "
        "Si no encuentras un valor razonable, devuelve value:null y confidence:0. "
        "IMPORTANTE: Devuelve ÚNICAMENTE el objeto JSON, nada más."
    )

    user = {
        "task": "Completar campos de un formulario detectados automáticamente.",
        "targets": targets,
        "knowledge_base": kb_raw,
        "output_schema": {
            "updates": [
                {
                    "kind": "bracket|underscore|table_cell|table_cell_underscore",
                    "token": "[...]",
                    "where": "paragraph:X / table:Y row:Z col:W ...",
                    "label": "texto del campo",
                    "value": "valor final o null",
                    "confidence": "0 a 1"
                }
            ]
        },
        "rules": [
            "Para kind='bracket' debes devolver token EXACTO (incluyendo corchetes) y un value.",
            "Para kind='underscore' o 'table_cell_underscore' devuelve label y value.",
            "Para kind='table_cell' devuelve label exacto de la celda izquierda y el value.",
            "Si el campo es una opción Sí/No o un checklist y no se detectó como target, IGNÓRALO (MVP2 no marca checks).",
        ],
    }

    return system, json.dumps(user, ensure_ascii=False)
