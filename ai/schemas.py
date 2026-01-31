"""
Esquemas Pydantic para validación de datos y output estructurado de LangChain.
"""

from typing import List, Optional, Literal
from pydantic import BaseModel, Field


class FieldUpdate(BaseModel):
    """Representa una actualización de campo sugerida por la IA."""
    
    kind: Literal["bracket", "underscore", "table_cell", "table_cell_underscore", "checkbox", "highlighted"] = Field(
        description="Tipo de campo: bracket=[...], underscore=___, table_cell=celda de tabla, checkbox=casilla de verificación, highlighted=texto destacado"
    )
    token: Optional[str] = Field(
        default=None,
        description="Token exacto a reemplazar (para kind='bracket'). Incluir corchetes. Ej: '[Nombre empresa]'"
    )
    where: Optional[str] = Field(
        default=None,
        description="Ubicación del campo en el documento. Ej: 'paragraph:5' o 'table:0 row:2 col:1'"
    )
    label: str = Field(
        description="Etiqueta o descripción del campo que identifica qué dato se solicita"
    )
    value: Optional[str] = Field(
        default=None,
        description="Valor a insertar. Usar null si no se encuentra en la base de conocimiento"
    )
    confidence: float = Field(
        ge=0.0,
        le=1.0,
        description="Confianza de 0 a 1. Usar 0 si no se está seguro del valor"
    )
    reasoning: Optional[str] = Field(
        default=None,
        description="Breve explicación de por qué se eligió este valor (opcional)"
    )


class FormFillerResponse(BaseModel):
    """Respuesta estructurada del modelo de IA para rellenar formularios."""
    
    updates: List[FieldUpdate] = Field(
        default_factory=list,
        description="Lista de actualizaciones de campos del formulario"
    )
    warnings: Optional[List[str]] = Field(
        default=None,
        description="Advertencias sobre campos ambiguos o datos faltantes"
    )


class KnowledgeBaseEntry(BaseModel):
    """Entrada de la base de conocimiento."""
    
    attribute: str = Field(description="Nombre del atributo o campo")
    value: str = Field(description="Valor del atributo")
    aliases: Optional[List[str]] = Field(
        default=None,
        description="Nombres alternativos para este atributo"
    )


class DocumentField(BaseModel):
    """Campo detectado en el documento que necesita ser llenado."""
    
    kind: str = Field(description="Tipo de campo detectado")
    where: str = Field(description="Ubicación en el documento")
    label: str = Field(description="Etiqueta del campo")
    sample: Optional[str] = Field(
        default=None,
        description="Muestra del contexto donde aparece el campo"
    )
    token: Optional[str] = Field(
        default=None,
        description="Token exacto (para brackets)"
    )


class ProcessingResult(BaseModel):
    """Resultado del procesamiento de un documento."""
    
    filled_by_rules: int = Field(description="Campos llenados por reglas")
    filled_by_ai: int = Field(description="Campos llenados por IA")
    pending: int = Field(description="Campos pendientes/saltados")
    total_fields: int = Field(description="Total de campos detectados")
