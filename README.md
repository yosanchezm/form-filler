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

- OpenAI (GPT-4o, GPT-4o-mini)
- Google Gemini (1.5 Flash, 1.5 Pro, 2.0 Flash)
- Anthropic Claude (3.5 Sonnet, 3.5 Haiku, 3 Opus)
- Groq (Llama 3.1, Mixtral)
- Together AI
- OpenRouter

## 📝 Características

- ✅ Relleno automático basado en reglas
- ✅ Detección de campos con underscores (`_____`)
- ✅ Detección de placeholders entre corchetes `[campo]`
- ✅ Relleno de tablas (label/valor)
- ✅ Completado opcional con IA
- ✅ Umbral de confianza configurable
- ✅ Descarga directa del resultado

## 🛠️ Buenas Prácticas Implementadas

1. **Separación de responsabilidades**: Cada módulo tiene una función específica
2. **Imports explícitos**: Uso de `__init__.py` para controlar la API pública
3. **Documentación**: Docstrings en funciones y módulos
4. **Type hints**: Anotaciones de tipos para mejor mantenibilidad
5. **Configuración centralizada**: Constantes en un solo lugar
6. **Modularidad**: Fácil de extender y testear

## 📄 Licencia

Proyecto personal de automatización.
