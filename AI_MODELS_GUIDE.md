# Guía de Modelos de IA Disponibles

## 🤖 Proveedores y Modelos Soportados (Enero 2026)

### OpenAI
- **Modelos recomendados:**
  - `gpt-4o-mini` - Rápido y económico (RECOMENDADO)
  - `gpt-4o` - Más capaz pero más costoso
  - `gpt-4-turbo` - Alternativa
- **API Key:** Desde https://platform.openai.com/api-keys
- **Pricing:** ~$0.15-0.60 por 1M tokens

### Google Gemini
- **Modelos recomendados:**
  - `gemini-1.5-flash-latest` - Rápido y económico (RECOMENDADO)
  - `gemini-1.5-pro-latest` - Más capaz
  - `gemini-2.0-flash-exp` - Experimental
- **API Key:** Desde https://makersuite.google.com/app/apikey
- **Pricing:** Gratis hasta cierto límite, luego $0.10-0.40 por 1M tokens
- **Notas:** 
  - Usa API v1 (no v1beta)
  - Nombres de modelos incluyen `-latest` o `-exp`

### Anthropic Claude
- **Modelos recomendados:**
  - `claude-3-5-haiku-20241022` - Rápido y económico
  - `claude-3-5-sonnet-20241022` - Mejor balance (RECOMENDADO)
  - `claude-3-opus-20240229` - Más capaz
- **API Key:** Desde https://console.anthropic.com/
- **Pricing:** ~$3-15 por 1M tokens

### Groq (ultra rápido)
- **Modelos recomendados:**
  - `llama-3.1-8b-instant` - Ultra rápido, gratis
  - `llama-3.1-70b-versatile` - Más capaz, gratis
  - `mixtral-8x7b-32768` - Alternativa
- **API Key:** Desde https://console.groq.com/
- **Pricing:** GRATIS (con límites)
- **Notas:** Extremadamente rápido, ideal para desarrollo

### Together AI
- **Modelos recomendados:**
  - `meta-llama/Llama-3.1-70B-Instruct-Turbo`
  - `mistralai/Mixtral-8x7B-Instruct-v0.1`
- **API Key:** Desde https://api.together.xyz/
- **Pricing:** ~$0.20-0.90 por 1M tokens

### OpenRouter (agregador)
- **Modelos recomendados:**
  - `openai/gpt-4o-mini` - OpenAI a través de OpenRouter
  - `anthropic/claude-3.5-sonnet`
  - `google/gemini-1.5-pro`
- **API Key:** Desde https://openrouter.ai/keys
- **Pricing:** Variable según modelo
- **Notas:** Acceso a múltiples proveedores con una sola API key

## 🔧 Solución de Problemas Comunes

### Error 404: Not Found
**Causa:** Nombre de modelo incorrecto o no disponible
**Solución:** 
1. Verifica que el nombre del modelo sea exacto
2. Para Gemini, usa nombres con `-latest` o `-exp`
3. Consulta la documentación actualizada del proveedor

### Error 401: Unauthorized
**Causa:** API Key inválida o expirada
**Solución:**
1. Verifica que la API key sea correcta
2. Revisa que tenga permisos apropiados
3. Genera una nueva key si es necesario

### Error 429: Rate Limit
**Causa:** Has excedido el límite de requests
**Solución:**
1. Espera unos minutos
2. Considera usar Groq (límites más altos)
3. Actualiza tu plan en el proveedor

### La IA no devuelve JSON válido
**Causa:** Temperatura alta o modelo que no sigue instrucciones bien
**Solución:**
1. Baja temperatura a 0.0
2. Usa modelos más estables (gpt-4o-mini, claude-3-5-sonnet)
3. El código ahora limpia markdown automáticamente

## 💡 Recomendaciones por Caso de Uso

### Para Desarrollo/Testing
- **Groq** con `llama-3.1-8b-instant` - GRATIS y ultra rápido
- **Gemini** con `gemini-1.5-flash-latest` - Gratis hasta límite generoso

### Para Producción (Mejor Calidad)
- **OpenAI** con `gpt-4o-mini` - Balance precio/calidad
- **Claude** con `claude-3-5-sonnet-20241022` - Mejor seguimiento de instrucciones

### Para Máximo Ahorro
- **Groq** - Completamente gratis
- **Gemini** - Nivel gratuito generoso

### Para Máxima Velocidad
- **Groq** - Más rápido del mercado
- **Gemini Flash** - Muy rápido también

## 📝 Configuración en la App

1. Selecciona el proveedor en el sidebar
2. El modelo por defecto se carga automáticamente
3. Puedes cambiarlo por cualquiera de los listados arriba
4. Pega tu API Key (se usa solo localmente, no se guarda)
5. Ajusta temperatura (0.0 recomendado para JSON)
6. Ajusta umbral de confianza (0.75 recomendado)

## 🔄 Actualización de Modelos

Los proveedores actualizan sus modelos frecuentemente. Si un modelo deja de funcionar:

1. Consulta la documentación oficial del proveedor
2. Actualiza el nombre del modelo en la UI
3. O edita `ai/providers.py` para actualizar los hints

## 🆘 Ayuda Adicional

- **OpenAI:** https://platform.openai.com/docs
- **Gemini:** https://ai.google.dev/docs
- **Claude:** https://docs.anthropic.com/
- **Groq:** https://console.groq.com/docs
- **Together:** https://docs.together.ai/
- **OpenRouter:** https://openrouter.ai/docs
