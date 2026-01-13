"""
Ejemplos de uso de los módulos del proyecto.

Este archivo muestra cómo usar las diferentes partes del proyecto
de forma programática (sin la UI de Streamlit).
"""

# =========================
# Ejemplo 1: Uso básico sin IA
# =========================
from core.knowledge_base import load_kb_from_xlsx_path
from core.processor import run_mvp2

# Cargar KB
kb = load_kb_from_xlsx_path("knowledge/mi_base.xlsx")

# Leer documento
with open("mi_formulario.docx", "rb") as f:
    docx_bytes = f.read()

# Procesar solo con reglas (sin IA)
output_bytes, filled_rules, filled_ai, skipped = run_mvp2(
    docx_bytes=docx_bytes,
    kb=kb,
    use_ai=False,
    provider="",
    api_key="",
    model="",
    confidence_threshold=0.75,
    temperature=0.0
)

# Guardar resultado
with open("resultado.docx", "wb") as f:
    f.write(output_bytes)

print(f"Rellenados por reglas: {len(filled_rules)}")

# =========================
# Ejemplo 2: Uso con IA
# =========================
output_bytes, filled_rules, filled_ai, skipped = run_mvp2(
    docx_bytes=docx_bytes,
    kb=kb,
    use_ai=True,
    provider="OpenAI",
    api_key="sk-...",
    model="gpt-4o-mini",
    confidence_threshold=0.75,
    temperature=0.0
)

print(f"Rellenados por reglas: {len(filled_rules)}")
print(f"Rellenados por IA: {len(filled_ai)}")
print(f"Pendientes: {len(skipped)}")

# =========================
# Ejemplo 3: Uso de utilidades individuales
# =========================
from utils.text_utils import norm, first_underscore_span
from utils.docx_utils import extract_bracket_tokens_from_doc
from docx import Document

# Normalizar texto
texto_original = "Dirección de Correo Electrónico:"
texto_normalizado = norm(texto_original)
print(f"Original: {texto_original}")
print(f"Normalizado: {texto_normalizado}")

# Detectar underscores
texto_con_underscores = "Nombre: _____________"
span = first_underscore_span(texto_con_underscores)
if span:
    print(f"Underscores encontrados en posición: {span}")

# Extraer tokens de documento
doc = Document("mi_formulario.docx")
tokens = extract_bracket_tokens_from_doc(doc)
print(f"Tokens encontrados: {tokens}")

# =========================
# Ejemplo 4: Búsqueda en KB
# =========================
from core.knowledge_base import find_value_for_label

kb_norm = kb["__norm__"]

valor = find_value_for_label("correo electronico", kb_norm)
print(f"Valor encontrado: {valor}")

# =========================
# Ejemplo 5: Crear KB programáticamente
# =========================
import pandas as pd

datos = {
    "Atributo": ["Nombre", "Email", "Teléfono"],
    "Valor": ["Juan Pérez", "juan@example.com", "+1234567890"]
}
df = pd.DataFrame(datos)
df.to_excel("mi_kb.xlsx", index=False)

# =========================
# Ejemplo 6: Uso directo de proveedores de IA
# =========================
from ai.providers import call_llm
from ai.prompts import build_prompt

targets = [
    {
        "kind": "bracket",
        "token": "[nombre completo]",
        "label": "nombre completo"
    }
]

kb_raw = kb["__raw__"]
system, user = build_prompt(targets, kb_raw)

# Llamar a un proveedor
response = call_llm(
    provider="OpenAI",
    api_key="sk-...",
    model="gpt-4o-mini",
    system=system,
    user=user,
    temperature=0.0
)

print(f"Respuesta de IA: {response}")

# =========================
# Ejemplo 7: Analizar eventos de relleno
# =========================
from models.events import FillEvent

# Los eventos retornados por run_mvp2 son objetos FillEvent
for event in filled_rules:
    print(f"Campo: {event.label}")
    print(f"Valor: {event.value}")
    print(f"Ubicación: {event.where}")
    print(f"Fuente: {event.source}")
    print(f"Confianza: {event.confidence}")
    print("---")
