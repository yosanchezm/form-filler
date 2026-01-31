"""
Gestión de la base de conocimiento con búsqueda semántica opcional.
"""

import io
import os
from typing import Dict, Optional, List, Tuple

import pandas as pd

from utils.text_utils import norm


# Intentar importar componentes de búsqueda semántica
SEMANTIC_SEARCH_AVAILABLE = False
try:
    from sentence_transformers import SentenceTransformer
    import numpy as np
    SEMANTIC_SEARCH_AVAILABLE = True
except ImportError:
    pass


# Cache global para el modelo de embeddings (evitar recarga)
_embedding_model = None


def get_embedding_model():
    """Obtiene o carga el modelo de embeddings (singleton)."""
    global _embedding_model
    if _embedding_model is None and SEMANTIC_SEARCH_AVAILABLE:
        # Modelo multilingüe ligero, bueno para español
        _embedding_model = SentenceTransformer('paraphrase-multilingual-MiniLM-L12-v2')
    return _embedding_model


def load_kb_from_xlsx_bytes(xlsx_bytes: bytes) -> Dict[str, Dict[str, str]]:
    """
    Carga la base de conocimiento desde bytes de un archivo XLSX.
    
    El XLSX debe contener columnas 'Atributo' y 'Valor'.
    
    Returns:
        Dict con claves '__raw__', '__norm__' y opcionalmente '__embeddings__'.
    """
    df = pd.read_excel(io.BytesIO(xlsx_bytes))
    if "Atributo" not in df.columns or "Valor" not in df.columns:
        raise ValueError("El XLSX debe tener columnas 'Atributo' y 'Valor'.")

    kb_raw = {}
    kb_norm = {}
    attributes = []
    
    for _, row in df.iterrows():
        k = str(row["Atributo"]).replace("\n", " ").strip()
        v = row["Valor"]
        if pd.isna(v):
            v = ""
        else:
            v = str(v)
        kb_raw[k] = v
        kb_norm[norm(k)] = v
        attributes.append(k)
    
    result = {"__raw__": kb_raw, "__norm__": kb_norm, "__attributes__": attributes}
    
    # Generar embeddings si está disponible
    if SEMANTIC_SEARCH_AVAILABLE:
        model = get_embedding_model()
        if model and attributes:
            embeddings = model.encode(attributes, convert_to_numpy=True)
            result["__embeddings__"] = embeddings
    
    return result


def load_kb_from_xlsx_path(path: str) -> Dict[str, Dict[str, str]]:
    """
    Carga la base de conocimiento desde una ruta de archivo XLSX.
    """
    with open(path, "rb") as f:
        return load_kb_from_xlsx_bytes(f.read())


def find_value_for_label(label: str, kb_norm: Dict[str, str]) -> Optional[str]:
    """
    Busca un valor en la KB normalizada para un label dado.
    
    Intenta match exacto primero, luego búsqueda parcial.
    """
    label_n = norm(label)
    if not label_n:
        return None
    
    # Match exacto
    if label_n in kb_norm:
        return kb_norm[label_n]
    
    # Búsqueda parcial bidireccional
    for k_n, v in kb_norm.items():
        if label_n in k_n or k_n in label_n:
            return v
    
    return None


def find_value_semantic(
    label: str,
    kb: Dict[str, any],
    threshold: float = 0.5
) -> Optional[Tuple[str, str, float]]:
    """
    Búsqueda semántica en la KB usando embeddings.
    
    Args:
        label: Texto del label a buscar
        kb: Base de conocimiento con '__embeddings__' y '__attributes__'
        threshold: Umbral mínimo de similitud (0-1)
    
    Returns:
        Tupla (atributo_encontrado, valor, similitud) o None si no hay match
    """
    if not SEMANTIC_SEARCH_AVAILABLE:
        return None
    
    if "__embeddings__" not in kb or "__attributes__" not in kb:
        return None
    
    model = get_embedding_model()
    if model is None:
        return None
    
    embeddings = kb["__embeddings__"]
    attributes = kb["__attributes__"]
    kb_raw = kb["__raw__"]
    
    # Generar embedding del label
    label_embedding = model.encode([label], convert_to_numpy=True)[0]
    
    # Calcular similitud coseno
    similarities = np.dot(embeddings, label_embedding) / (
        np.linalg.norm(embeddings, axis=1) * np.linalg.norm(label_embedding)
    )
    
    # Encontrar mejor match
    best_idx = np.argmax(similarities)
    best_score = similarities[best_idx]
    
    if best_score >= threshold:
        best_attr = attributes[best_idx]
        return (best_attr, kb_raw[best_attr], float(best_score))
    
    return None


def find_value_hybrid(
    label: str,
    kb: Dict[str, any],
    semantic_threshold: float = 0.6
) -> Optional[Tuple[str, float]]:
    """
    Búsqueda híbrida: primero reglas, luego semántica.
    
    Args:
        label: Texto del label
        kb: Base de conocimiento completa
        semantic_threshold: Umbral para búsqueda semántica
    
    Returns:
        Tupla (valor, confianza) o None
    """
    kb_norm = kb.get("__norm__", {})
    
    # 1. Intento con reglas (confianza 1.0)
    value = find_value_for_label(label, kb_norm)
    if value is not None:
        return (value, 1.0)
    
    # 2. Intento con búsqueda semántica
    semantic_result = find_value_semantic(label, kb, semantic_threshold)
    if semantic_result:
        _, value, score = semantic_result
        return (value, score)
    
    return None


def get_kb_summary(kb: Dict[str, any]) -> Dict[str, any]:
    """
    Genera un resumen de la base de conocimiento.
    
    Returns:
        Dict con estadísticas de la KB
    """
    kb_raw = kb.get("__raw__", {})
    return {
        "total_entries": len(kb_raw),
        "attributes": list(kb_raw.keys()),
        "has_embeddings": "__embeddings__" in kb,
        "semantic_search_available": SEMANTIC_SEARCH_AVAILABLE,
    }

