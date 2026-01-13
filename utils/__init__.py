"""
Utilidades del proyecto.
"""

from .text_utils import norm, looks_empty_or_underscores, first_underscore_span, extract_label_before_underscores
from .docx_utils import (
    set_paragraph_text,
    replace_in_paragraph_all,
    fill_underscore_in_paragraph,
    iter_all_paragraphs,
    extract_bracket_tokens_from_doc
)

__all__ = [
    'norm',
    'looks_empty_or_underscores',
    'first_underscore_span',
    'extract_label_before_underscores',
    'set_paragraph_text',
    'replace_in_paragraph_all',
    'fill_underscore_in_paragraph',
    'iter_all_paragraphs',
    'extract_bracket_tokens_from_doc',
]
