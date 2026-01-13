"""
Gestión de la base de conocimiento.
"""

import io
from typing import Dict, Optional

import pandas as pd

from utils.text_utils import norm


def load_kb_from_xlsx_bytes(xlsx_bytes: bytes) -> Dict[str, Dict[str, str]]:
    """
    Carga la base de conocimiento desde bytes de un archivo XLSX.
    
    El XLSX debe contener columnas 'Atributo' y 'Valor'.
    
    Returns:
        Dict con claves '__raw__' y '__norm__' conteniendo versiones del KB.
    """
    df = pd.read_excel(io.BytesIO(xlsx_bytes))
    if "Atributo" not in df.columns or "Valor" not in df.columns:
        raise ValueError("El XLSX debe tener columnas 'Atributo' y 'Valor'.")

    kb_raw = {}
    kb_norm = {}
    for _, row in df.iterrows():
        k = str(row["Atributo"]).replace("\n", " ").strip()
        v = row["Valor"]
        kb_raw[k] = v
        kb_norm[norm(k)] = v
    return {"__raw__": kb_raw, "__norm__": kb_norm}


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
    if label_n in kb_norm:
        return kb_norm[label_n]
    for k_n, v in kb_norm.items():
        if label_n in k_n or k_n in label_n:
            return v
    return None
