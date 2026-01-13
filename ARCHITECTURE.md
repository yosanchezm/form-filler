# Arquitectura del Proyecto

## Vista General

```
┌─────────────────────────────────────────────────────────────────┐
│                         app.py (Entry Point)                     │
│                    Wrapper que llama a main()                    │
└────────────────────────────┬────────────────────────────────────┘
                             │
                             v
┌─────────────────────────────────────────────────────────────────┐
│                    ui/streamlit_app.py                           │
│              Interfaz de Usuario con Streamlit                   │
│  - Configuración de parámetros                                   │
│  - Upload de archivos                                            │
│  - Visualización de resultados                                   │
└────────┬─────────────────────────────────────────┬──────────────┘
         │                                         │
         v                                         v
┌────────────────────┐                    ┌────────────────────┐
│  config/settings   │                    │ core/knowledge_base│
│  - MIN_UNDERSCORES │                    │ - load_kb_*()      │
│  - Directorios     │                    │ - find_value_*()   │
└────────────────────┘                    └──────────┬─────────┘
                                                     │
         ┌───────────────────────────────────────────┘
         │
         v
┌─────────────────────────────────────────────────────────────────┐
│                      core/processor.py                           │
│                      run_mvp2() - Orquestador                    │
│  1. Carga documento DOCX                                         │
│  2. Llama a fill_bracket_placeholders()                          │
│  3. Llama a fill_paragraph_underscore_fields()                   │
│  4. Llama a fill_table_fields()                                  │
│  5. Si usa IA: construye prompt y llama LLM                      │
│  6. Aplica updates de IA                                         │
│  7. Guarda documento final                                       │
└────┬────────────────────────┬────────────────────┬──────────────┘
     │                        │                    │
     v                        v                    v
┌─────────────┐      ┌──────────────┐     ┌─────────────────────┐
│ core/filler │      │ ai/prompts   │     │   ai/providers      │
│ - fill_*()  │      │ - build_*()  │     │   - call_llm()      │
│ - apply_*() │      └──────────────┘     │   - PROVIDERS       │
└──────┬──────┘                           └─────────────────────┘
       │
       v
┌──────────────────────────────────────────────────────────────┐
│                    utils/docx_utils                           │
│  - set_paragraph_text()                                       │
│  - replace_in_paragraph_all()                                 │
│  - fill_underscore_in_paragraph()                             │
│  - iter_all_paragraphs()                                      │
│  - extract_bracket_tokens_from_doc()                          │
└────────────────────────┬─────────────────────────────────────┘
                         │
                         v
┌──────────────────────────────────────────────────────────────┐
│                    utils/text_utils                           │
│  - norm()                                                     │
│  - looks_empty_or_underscores()                               │
│  - first_underscore_span()                                    │
│  - extract_label_before_underscores()                         │
└──────────────────────────────────────────────────────────────┘

┌──────────────────────────────────────────────────────────────┐
│                     models/events                             │
│  - FillEvent (dataclass)                                      │
│    * where, label, value, source, confidence                  │
└──────────────────────────────────────────────────────────────┘
```

## Flujo de Datos

```
1. Usuario sube DOCX + KB (xlsx)
         ↓
2. ui/streamlit_app.py procesa inputs
         ↓
3. core/knowledge_base.py carga KB
         ↓
4. core/processor.py ejecuta run_mvp2()
         ↓
5. core/filler.py intenta rellenar con reglas
         ↓
6. Si hay campos pendientes y IA activada:
   - ai/prompts.py construye prompt
   - ai/providers.py llama al LLM
   - core/filler.py aplica updates
         ↓
7. Documento procesado se guarda
         ↓
8. ui/streamlit_app.py muestra resultados
```

## Principios de Diseño Aplicados

### 1. Separación de Responsabilidades (SoC)
- **UI**: Solo maneja interfaz (ui/)
- **Business Logic**: Procesamiento y reglas (core/)
- **Data**: Modelos (models/)
- **Utils**: Funciones auxiliares (utils/)
- **Config**: Configuración centralizada (config/)
- **AI**: Integraciones externas (ai/)

### 2. Modularidad
- Cada módulo puede ser importado y usado independientemente
- Fácil de testear componentes individuales
- Cambios en un módulo no afectan a otros

### 3. Single Responsibility Principle
- Cada archivo tiene una función clara y específica
- text_utils.py: solo operaciones de texto
- docx_utils.py: solo operaciones con documentos
- knowledge_base.py: solo gestión de KB

### 4. DRY (Don't Repeat Yourself)
- Código duplicado eliminado
- Funciones reutilizables en utils/
- Configuración en un solo lugar

### 5. Explícito sobre Implícito
- Imports explícitos en __init__.py
- Type hints en funciones
- Docstrings descriptivos

## Ventajas de la Nueva Estructura

✅ **Mantenibilidad**: Código organizado y fácil de encontrar
✅ **Escalabilidad**: Fácil agregar nuevos proveedores de IA o métodos de relleno
✅ **Testabilidad**: Cada módulo puede testearse de forma aislada
✅ **Legibilidad**: Estructura clara y documentada
✅ **Reutilización**: Componentes pueden usarse en otros proyectos
✅ **Colaboración**: Múltiples desarrolladores pueden trabajar en paralelo
