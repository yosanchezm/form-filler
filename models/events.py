"""
Modelos de datos del proyecto.
"""

from dataclasses import dataclass


@dataclass
class FillEvent:
    """
    Representa un evento de relleno de campo.
    """
    where: str
    label: str
    value: str
    source: str  # "rules" | "ai"
    confidence: float = 1.0
