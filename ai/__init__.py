"""
Módulo de IA - Versión mejorada con LangChain.
"""

from .providers import PROVIDERS, call_llm
from .prompts import build_prompt, build_prompt_for_document_type, build_validation_prompt
from .schemas import FormFillerResponse, FieldUpdate, DocumentField

# Intentar importar LangChain processor
try:
    from .langchain_processor import (
        call_llm_langchain,
        call_llm_with_structured_output,
        is_langchain_supported,
        get_supported_providers,
        get_provider_models,
        LANGCHAIN_PROVIDERS
    )
    LANGCHAIN_AVAILABLE = True
except ImportError:
    LANGCHAIN_AVAILABLE = False
    LANGCHAIN_PROVIDERS = {}

__all__ = [
    # Providers tradicionales
    'PROVIDERS', 
    'call_llm',
    # Prompts
    'build_prompt',
    'build_prompt_for_document_type',
    'build_validation_prompt',
    # Schemas
    'FormFillerResponse',
    'FieldUpdate',
    'DocumentField',
    # LangChain (si disponible)
    'LANGCHAIN_AVAILABLE',
    'LANGCHAIN_PROVIDERS',
]

# Agregar exports de LangChain si está disponible
if LANGCHAIN_AVAILABLE:
    __all__.extend([
        'call_llm_langchain',
        'call_llm_with_structured_output',
        'is_langchain_supported',
        'get_supported_providers',
        'get_provider_models',
    ])

