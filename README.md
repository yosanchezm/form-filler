# Form Filter - Rellenador de Formularios DOCX

Aplicación Streamlit para rellenar automáticamente formularios en documentos DOCX usando reglas basadas en una base de conocimiento y opcionalmente IA.

## 📁 Estructura del Proyecto

```
form_filter/
├── app.py                    # Punto de entrada principal
├── requirements.txt          # Dependencias del proyecto
├── config/
│   └── settings.py          # Configuración central
├── models/
│   ├── __init__.py
│   └── events.py            # Modelos de datos (FillEvent)
├── utils/
│   ├── __init__.py
│   ├── text_utils.py        # Utilidades de normalización de texto
│   └── docx_utils.py        # Utilidades de manipulación de DOCX
├── core/
│   ├── __init__.py
│   ├── knowledge_base.py    # Gestión de la base de conocimiento
│   ├── filler.py            # Lógica de relleno de campos
│   └── processor.py         # Procesador principal del documento
├── ai/
│   ├── __init__.py
│   ├── providers.py         # Proveedores de IA (OpenAI, Gemini, Claude, etc)
│   └── prompts.py           # Construcción de prompts
├── ui/
│   └── streamlit_app.py     # Interfaz de usuario con Streamlit
├── knowledge/               # Bases de conocimiento (.xlsx)
└── outputs/                 # Documentos generados
```

## 🚀 Instalación

1. Clona el repositorio o descarga los archivos
2. Crea un entorno virtual (recomendado):
   ```bash
   python -m venv .venv
   source .venv/bin/activate  # En macOS/Linux
   # o
   .venv\Scripts\activate  # En Windows
   ```
3. Instala las dependencias:
   ```bash
   pip install -r requirements.txt
   ```

## 📖 Uso

### Ejecutar la aplicación

```bash
streamlit run app.py
```

### Preparar la base de conocimiento

Crea un archivo Excel (.xlsx) con dos columnas:

- **Atributo**: El nombre del campo
- **Valor**: El valor correspondiente

Guárdalo en la carpeta `knowledge/`.

### Rellenar un formulario

1. Abre la aplicación en el navegador (se abrirá automáticamente)
2. Sube tu documento DOCX
3. Selecciona o sube una base de conocimiento
4. (Opcional) Activa la IA y configura el proveedor
5. Haz clic en "Generar DOCX de salida"

## 🧩 Módulos

### config/

Configuración centralizada del proyecto (constantes, directorios, etc).

### models/

Modelos de datos usados en el proyecto. Define `FillEvent` para representar eventos de relleno.

### utils/

Utilidades reutilizables:

- `text_utils.py`: Normalización de texto, detección de underscores
- `docx_utils.py`: Manipulación de párrafos, tablas y placeholders en DOCX

### core/

Lógica de negocio principal:

- `knowledge_base.py`: Carga y búsqueda en la base de conocimiento
- `filler.py`: Lógica de relleno de campos (brackets, underscores, tablas)
- `processor.py`: Orquestación del proceso completo

### ai/

Integración con modelos de IA:

- `providers.py`: Conectores para OpenAI, Gemini, Claude, Groq, Together, OpenRouter
- `prompts.py`: Construcción de prompts para los modelos

### ui/

Interfaz de usuario con Streamlit.

## 🤖 Proveedores de IA Soportados

### Con LangChain (Recomendado) 🦜

- **OpenAI** (GPT-4o, GPT-4o-mini, GPT-4-turbo)
- **Anthropic Claude** (Claude Sonnet 4, 3.5 Haiku, 3 Opus)
- **Google Gemini** (2.5 Flash, 2.0 Flash, 2.5 Pro)

### API Directa (Fallback)

- Groq (Llama 3.1, Mixtral)
- Together AI
- OpenRouter

## 📝 Características

### Detección de Campos

- ✅ Placeholders entre corchetes `[campo]`
- ✅ Campos con underscores (`_____`)
- ✅ Tablas label/valor
- ✅ Checkboxes (Sí/No, opciones múltiples)
- ✅ Campos de fecha con múltiples espacios
- ✅ Texto destacado (negrita, subrayado)

### Procesamiento Inteligente

- ✅ Relleno automático basado en reglas
- ✅ **Búsqueda semántica** en KB con embeddings
- ✅ Completado con IA (LangChain)
- ✅ **Output estructurado** garantizado
- ✅ Retry automático en caso de fallos
- ✅ Umbral de confianza configurable

### Interfaz

- ✅ Preview del documento antes de procesar
- ✅ Análisis de campos detectados
- ✅ Modo "solo reglas" sin IA
- ✅ Descarga directa del resultado

## 🆕 Novedades v2.0

### LangChain Integration

```python
# Output estructurado garantizado con Pydantic
from ai.schemas import FormFillerResponse, FieldUpdate

# Retry automático y manejo de errores
from ai.langchain_processor import call_llm_with_structured_output
```

### Búsqueda Semántica

```python
# Encuentra matches aunque las palabras no coincidan exactamente
from core.knowledge_base import find_value_hybrid

# "Razón social" encontrará "Nombre de la empresa"
result = find_value_hybrid("Razón social", kb)
```

### Nuevos Tipos de Campos

- `checkbox`: Sí/No, X, opciones múltiples
- `date_field`: Campos de fecha compuestos
- `highlighted`: Texto con formato especial

## 🛠️ Instalación de Dependencias

```bash
# Instalar todas las dependencias (incluyendo LangChain)
pip install -r requirements.txt

# Solo dependencias básicas (sin búsqueda semántica)
pip install streamlit python-docx pandas openpyxl requests
```

## 🛠️ Buenas Prácticas Implementadas

1. **Separación de responsabilidades**: Cada módulo tiene una función específica
2. **Imports explícitos**: Uso de `__init__.py` para controlar la API pública
3. **Documentación**: Docstrings en funciones y módulos
4. **Type hints**: Anotaciones de tipos para mejor mantenibilidad
5. **Configuración centralizada**: Constantes en un solo lugar
6. **Modularidad**: Fácil de extender y testear
7. **Output estructurado**: Pydantic schemas para validación
8. **Graceful degradation**: Funciona sin LangChain usando API directa

## 📄 Licencia

Proyecto personal de automatización.
