"""
Prompts para interacción con modelos de IA - Versión mejorada.
"""

import json
from typing import Dict, List, Any, Tuple


# Prompt del sistema mejorado con más contexto
SYSTEM_PROMPT_ES = """Eres un asistente experto en completar formularios oficiales colombianos.

Tu tarea es analizar los campos detectados en un formulario y proponer valores basándote ÚNICAMENTE en la base de conocimiento proporcionada.

## REGLAS ESTRICTAS:

1. **NO INVENTES VALORES**: Solo usa información que existe en la base de conocimiento.
   - Si no encuentras un valor apropiado, devuelve value: null y confidence: 0

2. **TIPOS DE CAMPOS**:
   - `bracket`: Tokens como [Nombre empresa]. Debes devolver el token EXACTO incluyendo corchetes.
   - `underscore`: Campos con líneas (____). Devuelve el valor que va sobre la línea.
   - `table_cell`: Celdas de tabla vacías. El label es el texto de la celda izquierda.
   - `checkbox`: Campos Sí/No o listas de opciones. El value debe ser "Sí", "No", "X" o la opción marcada.
   - `date_field`: Campos de fecha con múltiples espacios. Devuelve la fecha completa.
   - `highlighted`: Texto destacado que debe ser reemplazado.

3. **FORMATO DE FECHAS**: 
   - Para fechas colombianas usa formato: "día de mes de año" (ej: "15 de enero de 2026")
   - Si hay campos separados (día/mes/año), usa valores individuales.

4. **CHECKBOXES Y OPCIONES**:
   - Para Sí/No: value = "Sí" o "No"
   - Para marcar con X: value = "X"
   - Para listas de opciones: value = nombre de la opción que aplica

5. **CONFIANZA (confidence)**:
   - 1.0: Match exacto con la base de conocimiento
   - 0.8-0.9: Match semántico muy probable
   - 0.5-0.7: Match parcial, podría requerir revisión humana
   - 0.0-0.4: No encontrado o muy incierto

## IMPORTANTE:
- Devuelve SOLO JSON válido, sin markdown, sin texto extra, sin explicaciones.
- El JSON debe tener la estructura exacta del schema proporcionado.
"""

SYSTEM_PROMPT_SIMPLE = """Eres un asistente experto en completar formularios. 
Debes devolver SOLO JSON válido (sin markdown, sin texto extra, sin explicaciones). 
No inventes valores: usa únicamente la base de conocimiento. 
Si no encuentras un valor razonable, devuelve value:null y confidence:0. 
IMPORTANTE: Devuelve ÚNICAMENTE el objeto JSON, nada más."""


def build_prompt(
    targets: List[Dict[str, Any]], 
    kb_raw: Dict[str, Any],
    use_detailed_prompt: bool = True
) -> Tuple[str, str]:
    """
    Construye el prompt (system, user) para pedirle al modelo un JSON de updates.
    
    Args:
        targets: Lista de campos pendientes de llenar
        kb_raw: Base de conocimiento sin normalizar
        use_detailed_prompt: Si usar el prompt detallado (mejor para modelos potentes)
    
    Returns:
        (system_message, user_message)
    """
    system = SYSTEM_PROMPT_ES if use_detailed_prompt else SYSTEM_PROMPT_SIMPLE

    user = {
        "task": "Completar campos de un formulario detectados automáticamente.",
        "targets": targets,
        "knowledge_base": kb_raw,
        "output_schema": {
            "updates": [
                {
                    "kind": "bracket|underscore|table_cell|table_cell_underscore|checkbox|date_field|highlighted",
                    "token": "[...] (solo para kind='bracket')",
                    "where": "paragraph:X / table:Y row:Z col:W ...",
                    "label": "texto del campo o etiqueta",
                    "value": "valor final o null si no se encuentra",
                    "confidence": "número de 0 a 1",
                    "reasoning": "breve explicación (opcional)"
                }
            ],
            "warnings": ["lista de advertencias si hay campos ambiguos (opcional)"]
        },
        "rules": [
            "Para kind='bracket' debes devolver token EXACTO (incluyendo corchetes) y un value.",
            "Para kind='underscore' o 'table_cell_underscore' devuelve label y value.",
            "Para kind='table_cell' devuelve label exacto de la celda izquierda y el value.",
            "Para kind='checkbox' devuelve 'Sí', 'No' o 'X' según corresponda.",
            "Para kind='date_field' devuelve la fecha en formato colombiano.",
            "Para kind='highlighted' devuelve el texto de reemplazo.",
            "Si hay opciones múltiples (ej: Persona natural/jurídica), indica cuál aplica según la KB.",
        ],
    }

    return system, json.dumps(user, ensure_ascii=False, indent=2)


def build_prompt_for_specific_fields(
    targets: List[Dict[str, Any]],
    kb_raw: Dict[str, Any],
    field_types: List[str]
) -> Tuple[str, str]:
    """
    Construye un prompt específico para ciertos tipos de campos.
    
    Útil cuando quieres procesar solo checkboxes, solo fechas, etc.
    
    Args:
        targets: Lista de campos
        kb_raw: Base de conocimiento
        field_types: Lista de tipos a incluir (ej: ["checkbox", "date_field"])
    
    Returns:
        (system_message, user_message)
    """
    # Filtrar targets por tipo
    filtered_targets = [t for t in targets if t.get("kind") in field_types]
    
    if not filtered_targets:
        return "", ""
    
    return build_prompt(filtered_targets, kb_raw, use_detailed_prompt=True)


def build_validation_prompt(
    filled_events: List[Dict[str, Any]],
    kb_raw: Dict[str, Any]
) -> Tuple[str, str]:
    """
    Construye un prompt para validar campos ya llenados.
    
    Útil para revisión de calidad.
    
    Args:
        filled_events: Lista de eventos de llenado a validar
        kb_raw: Base de conocimiento
    
    Returns:
        (system_message, user_message)
    """
    system = """Eres un revisor experto de formularios. 
Tu tarea es verificar que los valores insertados son correctos según la base de conocimiento.

Devuelve SOLO JSON con el siguiente formato:
{
    "validations": [
        {
            "label": "campo revisado",
            "current_value": "valor actual",
            "is_correct": true/false,
            "suggested_value": "valor correcto si is_correct=false",
            "reason": "explicación breve"
        }
    ],
    "overall_quality": "good|needs_review|poor"
}
"""

    user = {
        "task": "Validar campos llenados en un formulario",
        "filled_fields": filled_events,
        "knowledge_base": kb_raw
    }

    return system, json.dumps(user, ensure_ascii=False, indent=2)


# Prompts especializados por tipo de documento
DOCUMENT_TYPE_PROMPTS = {
    "contrato": {
        "context": "Este es un contrato legal colombiano.",
        "special_fields": ["NIT", "razón social", "representante legal", "cédula"],
        "format_hints": {
            "NIT": "Formato: XXXXXXXXX-X",
            "cédula": "Solo números",
            "fecha": "DD de MMMM de AAAA"
        }
    },
    "certificacion": {
        "context": "Esta es una certificación oficial.",
        "special_fields": ["revisor fiscal", "tarjeta profesional", "fecha de constitución"],
        "format_hints": {
            "tarjeta_profesional": "Número con código de ciudad",
        }
    },
    "propuesta": {
        "context": "Este es un documento de propuesta/licitación.",
        "special_fields": ["proponente", "objeto del contrato", "valor"],
        "format_hints": {
            "valor": "Formato moneda colombiana con separadores de miles"
        }
    }
}


def build_prompt_for_document_type(
    targets: List[Dict[str, Any]],
    kb_raw: Dict[str, Any],
    document_type: str
) -> Tuple[str, str]:
    """
    Construye un prompt especializado según el tipo de documento.
    
    Args:
        targets: Lista de campos
        kb_raw: Base de conocimiento
        document_type: Tipo de documento (contrato, certificacion, propuesta)
    
    Returns:
        (system_message, user_message)
    """
    base_system, base_user = build_prompt(targets, kb_raw)
    
    if document_type in DOCUMENT_TYPE_PROMPTS:
        doc_config = DOCUMENT_TYPE_PROMPTS[document_type]
        
        # Agregar contexto específico
        system = base_system + f"\n\n## CONTEXTO DEL DOCUMENTO:\n{doc_config['context']}\n"
        
        # Agregar hints de formato
        if doc_config.get("format_hints"):
            system += "\n## FORMATOS ESPECIALES:\n"
            for field, hint in doc_config["format_hints"].items():
                system += f"- {field}: {hint}\n"
        
        return system, base_user
    
    return base_system, base_user

