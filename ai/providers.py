"""
Proveedores de modelos de IA (OpenAI, Gemini, Claude, etc).
"""

import json
from typing import Dict, Any

import requests


# Configuración de proveedores
PROVIDERS = {
    "OpenAI": {
        "base_url": "https://api.openai.com/v1/chat/completions",
        "models_hint": ["gpt-4o-mini", "gpt-4.1-mini", "gpt-4o"],
    },
    "Gemini (Google)": {
        # v1beta generateContent - Gemini 2.x (enero 2026)
        "base_url": "https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent",
        "models_hint": ["gemini-2.5-flash", "gemini-2.0-flash", "gemini-2.5-pro"],
    },
    "Claude (Anthropic)": {
        "base_url": "https://api.anthropic.com/v1/messages",
        "models_hint": ["claude-3-5-sonnet-20240620", "claude-3-5-haiku-20241022", "claude-3-opus-20240229"],
    },
    "Groq": {
        "base_url": "https://api.groq.com/openai/v1/chat/completions",
        "models_hint": ["llama-3.1-70b-versatile", "llama-3.1-8b-instant", "mixtral-8x7b-32768"],
    },
    "Together": {
        "base_url": "https://api.together.xyz/v1/chat/completions",
        "models_hint": ["meta-llama/Llama-3.1-70B-Instruct-Turbo", "mistralai/Mixtral-8x7B-Instruct-v0.1"],
    },
    "OpenRouter": {
        "base_url": "https://openrouter.ai/api/v1/chat/completions",
        "models_hint": ["openai/gpt-4o-mini", "anthropic/claude-3.5-sonnet", "google/gemini-1.5-pro"],
    },
}


def call_llm(provider: str, api_key: str, model: str, system: str, user: str, temperature: float = 0.0) -> Dict[str, Any]:
    """
    Hace una llamada al proveedor de IA y devuelve el JSON parseado.
    
    Args:
        provider: Nombre del proveedor
        api_key: Clave API
        model: Nombre del modelo
        system: Mensaje de sistema
        user: Mensaje de usuario
        temperature: Temperatura del modelo (0.0 = determinista)
    
    Returns:
        Respuesta parseada como dict
    
    Raises:
        ValueError: Si el proveedor no es soportado
        requests.HTTPError: Si hay error en la llamada HTTP
        json.JSONDecodeError: Si la respuesta no es JSON válido
    """
    if provider == "OpenAI":
        headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}
        payload = {
            "model": model,
            "temperature": temperature,
            "messages": [
                {"role": "system", "content": system},
                {"role": "user", "content": user},
            ],
        }
        r = requests.post(PROVIDERS[provider]["base_url"], headers=headers, json=payload, timeout=60)
        r.raise_for_status()
        content = r.json()["choices"][0]["message"]["content"]
        try:
            return json.loads(content)
        except json.JSONDecodeError as e:
            raise ValueError(f"OpenAI devolvió texto no-JSON. Error: {e}\nRespuesta cruda:\n{content[:2000]}")

    if provider in ("Groq", "Together", "OpenRouter"):
        # OpenAI-compatible chat completions
        headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}
        payload = {
            "model": model,
            "temperature": temperature,
            "messages": [
                {"role": "system", "content": system},
                {"role": "user", "content": user},
            ],
        }
        r = requests.post(PROVIDERS[provider]["base_url"], headers=headers, json=payload, timeout=60)
        r.raise_for_status()
        content = r.json()["choices"][0]["message"]["content"]
        try:
            return json.loads(content)
        except json.JSONDecodeError as e:
            raise ValueError(f"{provider} devolvió texto no-JSON. Error: {e}\nRespuesta cruda:\n{content[:2000]}")

    if provider == "Gemini (Google)":
        # Google: key in query param, API v1
        url = PROVIDERS[provider]["base_url"].format(model=model) + f"?key={api_key}"
        payload = {
            "contents": [
                {"role": "user", "parts": [{"text": system + "\n\n" + user}]}
            ],
            "generationConfig": {
                "temperature": temperature,
                "maxOutputTokens": 8192,
            },
        }
        r = requests.post(url, json=payload, timeout=60)
        r.raise_for_status()
        # Gemini devuelve texto; esperamos JSON puro
        response_data = r.json()
        if "candidates" not in response_data or not response_data["candidates"]:
            raise ValueError(f"Gemini no devolvió candidatos. Respuesta completa: {json.dumps(response_data, indent=2)}")
        
        candidate = response_data["candidates"][0]
        finish_reason = candidate.get("finishReason", "")
        
        # Verificar si la respuesta fue truncada
        if finish_reason == "MAX_TOKENS":
            raise ValueError(f"Gemini truncó la respuesta por límite de tokens. Respuesta parcial: {json.dumps(response_data, indent=2)[:1000]}")
        
        raw_text = candidate["content"]["parts"][0]["text"]
        # Limpiar markdown si viene con ```json
        text = raw_text.strip()
        if text.startswith("```json"):
            text = text[7:]
        if text.startswith("```"):
            text = text[3:]
        if text.endswith("```"):
            text = text[:-3]
        text = text.strip()
        try:
            return json.loads(text)
        except json.JSONDecodeError as e:
            error_msg = (
                f"Gemini devolvió texto no-JSON. Error: {e}\\n"
                f"Longitud del texto original: {len(raw_text)} chars\\n"
                f"Longitud del texto limpio: {len(text)} chars\\n"
                f"Finish reason: {finish_reason}\\n"
                f"\\nTexto original (primeros 2000 chars):\\n{raw_text[:2000]}\\n"
                f"\\nTexto limpio (primeros 2000 chars):\\n{text[:2000]}\\n"
                f"\\nÚltimos 500 chars del texto limpio:\\n...{text[-500:]}"
            )
            raise ValueError(error_msg)

    if provider == "Claude (Anthropic)":
        headers = {
            "x-api-key": api_key,
            "anthropic-version": "2023-06-01",
            "content-type": "application/json",
        }
        payload = {
            "model": model,
            "max_tokens": 2000,
            "temperature": temperature,
            "system": system,
            "messages": [{"role": "user", "content": user}],
        }
        r = requests.post(PROVIDERS[provider]["base_url"], headers=headers, json=payload, timeout=60)
        r.raise_for_status()
        # Claude devuelve array de content blocks; esperamos JSON puro en el texto
        blocks = r.json().get("content", [])
        text = ""
        for b in blocks:
            if b.get("type") == "text":
                text += b.get("text", "")
        try:
            return json.loads(text)
        except json.JSONDecodeError as e:
            raise ValueError(f"Claude devolvió texto no-JSON. Error: {e}\nRespuesta cruda:\n{text[:2000]}")

    raise ValueError(f"Proveedor no soportado: {provider}")
