"""
Módulo core del proyecto.
"""

from .knowledge_base import load_kb_from_xlsx_bytes, load_kb_from_xlsx_path, find_value_for_label
from .filler import fill_bracket_placeholders, fill_paragraph_underscore_fields, fill_table_fields, apply_ai_updates
from .processor import run_mvp2

__all__ = [
    'load_kb_from_xlsx_bytes',
    'load_kb_from_xlsx_path',
    'find_value_for_label',
    'fill_bracket_placeholders',
    'fill_paragraph_underscore_fields',
    'fill_table_fields',
    'apply_ai_updates',
    'run_mvp2',
]
