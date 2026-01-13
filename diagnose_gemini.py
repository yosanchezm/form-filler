"""
Script de diagnóstico para Gemini API.
"""

import requests
import json

def test_gemini_endpoint(api_key: str):
    """Prueba diferentes endpoints y modelos de Gemini."""
    
    print("=" * 70)
    print("DIAGNÓSTICO DE GEMINI API")
    print("=" * 70)
    
    # Diferentes combinaciones a probar
    tests = [
        ("v1beta", "gemini-1.5-flash"),
        ("v1beta", "gemini-1.5-pro"),
        ("v1beta", "gemini-pro"),
        ("v1", "gemini-1.5-flash"),
        ("v1", "gemini-pro"),
    ]
    
    for version, model in tests:
        print(f"\n{'─' * 70}")
        print(f"Probando: {version} / {model}")
        print(f"{'─' * 70}")
        
        url = f"https://generativelanguage.googleapis.com/{version}/models/{model}:generateContent?key={api_key}"
        
        payload = {
            "contents": [
                {
                    "parts": [
                        {"text": "Hola, responde solo 'OK'"}
                    ]
                }
            ]
        }
        
        try:
            response = requests.post(url, json=payload, timeout=10)
            
            print(f"Status Code: {response.status_code}")
            
            if response.status_code == 200:
                print("✅ ÉXITO!")
                data = response.json()
                if "candidates" in data:
                    text = data["candidates"][0]["content"]["parts"][0]["text"]
                    print(f"Respuesta: {text}")
                print(f"Respuesta completa: {json.dumps(data, indent=2)}")
                return version, model
            else:
                print(f"❌ ERROR {response.status_code}")
                try:
                    error_data = response.json()
                    print(f"Error: {json.dumps(error_data, indent=2)}")
                except:
                    print(f"Respuesta: {response.text}")
        
        except Exception as e:
            print(f"❌ EXCEPCIÓN: {e}")
    
    # Intentar listar modelos disponibles
    print(f"\n{'=' * 70}")
    print("INTENTANDO LISTAR MODELOS DISPONIBLES")
    print(f"{'=' * 70}")
    
    for version in ["v1beta", "v1"]:
        list_url = f"https://generativelanguage.googleapis.com/{version}/models?key={api_key}"
        print(f"\nListando modelos en {version}...")
        
        try:
            response = requests.get(list_url, timeout=10)
            if response.status_code == 200:
                data = response.json()
                print(f"✅ Modelos disponibles en {version}:")
                if "models" in data:
                    for model in data["models"]:
                        name = model.get("name", "N/A")
                        display_name = model.get("displayName", "N/A")
                        print(f"  - {name} ({display_name})")
            else:
                print(f"❌ Error {response.status_code}: {response.text[:200]}")
        except Exception as e:
            print(f"❌ Excepción: {e}")
    
    return None, None


if __name__ == "__main__":
    print("\n🔍 Script de Diagnóstico para Gemini API\n")
    api_key = input("Ingresa tu API Key de Gemini: ").strip()
    
    if not api_key:
        print("❌ API Key requerida")
    else:
        working_version, working_model = test_gemini_endpoint(api_key)
        
        if working_version and working_model:
            print(f"\n{'=' * 70}")
            print("✅ CONFIGURACIÓN QUE FUNCIONA:")
            print(f"   Versión: {working_version}")
            print(f"   Modelo: {working_model}")
            print(f"{'=' * 70}")
        else:
            print(f"\n{'=' * 70}")
            print("❌ No se encontró una configuración funcional")
            print("   Posibles causas:")
            print("   1. API Key inválida o sin permisos")
            print("   2. Modelos no disponibles en tu región")
            print("   3. API Key necesita habilitación de Gemini API")
            print(f"{'=' * 70}")
            print("\n💡 Verifica:")
            print("   - https://makersuite.google.com/app/apikey")
            print("   - https://console.cloud.google.com/apis/library/generativelanguage.googleapis.com")
