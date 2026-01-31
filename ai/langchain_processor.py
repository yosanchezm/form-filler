"""
Procesador de IA usando LangChain para mayor robustez y flexibilidad.
"""

import json
from typing import Dict, List, Any, Optional

from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import PydanticOutputParser
from langchain_core.runnables import RunnablePassthrough
from langchain_openai import ChatOpenAI
from langchain_anthropic import ChatAnthropic
from langchain_google_genai import ChatGoogleGenerativeAI
from tenacity import retry, stop_after_attempt, wait_exponential

from ai.schemas import FormFillerResponse, FieldUpdate


# Mapeo de proveedores a clases de LangChain
LANGCHAIN_PROVIDERS = {
    "OpenAI": {
        "class": ChatOpenAI,
        "api_key_param": "api_key",
        "models": ["gpt-4o-mini", "gpt-4.1-mini", "gpt-4o", "gpt-4-turbo"],
    },
    "Claude (Anthropic)": {
        "class": ChatAnthropic,
        "api_key_param": "api_key",
        "models": ["claude-sonnet-4-20250514", "claude-3-5-haiku-20241022", "claude-3-opus-20240229"],
    },
    "Gemini (Google)": {
        "class": ChatGoogleGenerativeAI,
        "api_key_param": "google_api_key",
        "models": ["gemini-2.5-flash", "gemini-2.0-flash", "gemini-2.5-pro"],
    },
}


# Prompt template mejorado para LangChain
SYSTEM_TEMPLATE = """Eres un asistente experto en completar formularios oficiales colombianos.

Tu tarea es analizar los campos detectados en un formulario y proponer valores basándote ÚNICAMENTE en la base de conocimiento proporcionada.

REGLAS ESTRICTAS:
1. NUNCA inventes valores. Solo usa información de la base de conocimiento.
2. Si no encuentras un valor apropiado, devuelve value=null y confidence=0.
3. Para campos de tipo checkbox (Sí/No), el value debe ser "X" o vacío.
4. Mantén el formato exacto de los tokens para kind='bracket'.
5. Asigna confidence según qué tan seguro estás del mapeo:
   - 1.0: Match exacto con la KB
   - 0.8-0.9: Match semántico muy probable
   - 0.5-0.7: Match parcial, podría requerir revisión
   - 0.0-0.4: No encontrado o muy incierto

{format_instructions}
"""

USER_TEMPLATE = """## CAMPOS A COMPLETAR:
{targets_json}

## BASE DE CONOCIMIENTO DISPONIBLE:
{knowledge_base_json}

Analiza cada campo y proporciona los valores correspondientes de la base de conocimiento.
Si un campo tiene múltiples underscores separados (como "a los ____ días del mes de ____ de 20__"), 
identifica cada parte y proporciona el valor completo apropiado.
"""


def get_langchain_model(
    provider: str,
    api_key: str,
    model: str,
    temperature: float = 0.0
):
    """
    Obtiene una instancia del modelo LangChain según el proveedor.
    
    Args:
        provider: Nombre del proveedor (OpenAI, Claude (Anthropic), Gemini (Google))
        api_key: Clave API
        model: Nombre del modelo
        temperature: Temperatura (0.0 = determinista)
    
    Returns:
        Instancia del modelo LangChain
    
    Raises:
        ValueError: Si el proveedor no es soportado
    """
    if provider not in LANGCHAIN_PROVIDERS:
        raise ValueError(
            f"Proveedor '{provider}' no soportado por LangChain. "
            f"Disponibles: {list(LANGCHAIN_PROVIDERS.keys())}"
        )
    
    config = LANGCHAIN_PROVIDERS[provider]
    model_class = config["class"]
    api_key_param = config["api_key_param"]
    
    # Configuración común
    kwargs = {
        api_key_param: api_key,
        "model": model,
        "temperature": temperature,
    }
    
    # Configuraciones específicas por proveedor
    if provider == "OpenAI":
        kwargs["max_tokens"] = 4096
    elif provider == "Claude (Anthropic)":
        kwargs["max_tokens"] = 4096
    elif provider == "Gemini (Google)":
        kwargs["max_output_tokens"] = 8192
    
    return model_class(**kwargs)


def create_form_filler_chain(
    provider: str,
    api_key: str,
    model: str,
    temperature: float = 0.0
):
    """
    Crea una cadena LangChain para rellenar formularios con output estructurado.
    
    Returns:
        Chain configurada que devuelve FormFillerResponse
    """
    # Parser de output estructurado
    parser = PydanticOutputParser(pydantic_object=FormFillerResponse)
    
    # Obtener modelo
    llm = get_langchain_model(provider, api_key, model, temperature)
    
    # Crear prompt template
    prompt = ChatPromptTemplate.from_messages([
        ("system", SYSTEM_TEMPLATE),
        ("human", USER_TEMPLATE),
    ])
    
    # Crear chain con output estructurado
    chain = (
        {
            "targets_json": lambda x: json.dumps(x["targets"], ensure_ascii=False, indent=2),
            "knowledge_base_json": lambda x: json.dumps(x["knowledge_base"], ensure_ascii=False, indent=2),
            "format_instructions": lambda _: parser.get_format_instructions(),
        }
        | prompt
        | llm
        | parser
    )
    
    return chain


@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=2, max=10),
    reraise=True
)
def call_llm_langchain(
    provider: str,
    api_key: str,
    model: str,
    targets: List[Dict[str, Any]],
    knowledge_base: Dict[str, Any],
    temperature: float = 0.0
) -> FormFillerResponse:
    """
    Llama al LLM usando LangChain con output estructurado y retry automático.
    
    Args:
        provider: Proveedor de IA
        api_key: Clave API
        model: Modelo a usar
        targets: Lista de campos a completar
        knowledge_base: Base de conocimiento (raw)
        temperature: Temperatura del modelo
    
    Returns:
        FormFillerResponse con las actualizaciones propuestas
    
    Raises:
        ValueError: Si el proveedor no es soportado
        Exception: Errores de API después de reintentos
    """
    chain = create_form_filler_chain(provider, api_key, model, temperature)
    
    result = chain.invoke({
        "targets": targets,
        "knowledge_base": knowledge_base,
    })
    
    return result


def call_llm_with_structured_output(
    provider: str,
    api_key: str,
    model: str,
    targets: List[Dict[str, Any]],
    knowledge_base: Dict[str, Any],
    temperature: float = 0.0
) -> Dict[str, Any]:
    """
    Versión que devuelve dict para compatibilidad con código existente.
    
    Returns:
        Dict con clave 'updates' conteniendo lista de actualizaciones
    """
    try:
        response = call_llm_langchain(
            provider=provider,
            api_key=api_key,
            model=model,
            targets=targets,
            knowledge_base=knowledge_base,
            temperature=temperature
        )
        
        # Convertir a dict para compatibilidad
        return {
            "updates": [update.model_dump() for update in response.updates],
            "warnings": response.warnings
        }
    
    except Exception as e:
        # Log del error para debugging
        print(f"Error en LangChain call: {e}")
        raise


def is_langchain_supported(provider: str) -> bool:
    """Verifica si un proveedor tiene soporte nativo de LangChain."""
    return provider in LANGCHAIN_PROVIDERS


def get_supported_providers() -> List[str]:
    """Retorna lista de proveedores soportados por LangChain."""
    return list(LANGCHAIN_PROVIDERS.keys())


def get_provider_models(provider: str) -> List[str]:
    """Retorna lista de modelos sugeridos para un proveedor."""
    if provider in LANGCHAIN_PROVIDERS:
        return LANGCHAIN_PROVIDERS[provider]["models"]
    return []
