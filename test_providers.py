"""
Script de prueba para verificar conectividad con proveedores de IA.

Uso:
    python test_providers.py
"""

from ai.providers import PROVIDERS, call_llm

def test_provider(provider_name: str, api_key: str, model: str = None):
    """
    Prueba la conectividad con un proveedor de IA.
    """
    if not model:
        model = PROVIDERS[provider_name]["models_hint"][0]
    
    print(f"\n{'='*60}")
    print(f"Probando: {provider_name}")
    print(f"Modelo: {model}")
    print(f"{'='*60}")
    
    system = "Eres un asistente útil. Devuelve solo JSON válido."
    user = '{"task": "Responde con un JSON que tenga una clave \\"status\\" con valor \\"ok\\" y una clave \\"message\\" con un saludo corto."}'
    
    try:
        response = call_llm(
            provider=provider_name,
            api_key=api_key,
            model=model,
            system=system,
            user=user,
            temperature=0.0
        )
        print("✅ ÉXITO!")
        print(f"Respuesta: {response}")
        return True
    except Exception as e:
        print(f"❌ ERROR: {e}")
        return False


def main():
    """
    Función principal de prueba.
    """
    print("╔════════════════════════════════════════════════════════════╗")
    print("║  Prueba de Proveedores de IA - Form Filter                ║")
    print("╚════════════════════════════════════════════════════════════╝")
    print("\nEste script te permite probar la conectividad con cada proveedor.")
    print("Ingresa tu API key cuando se te solicite (se usa solo localmente).\n")
    
    # Lista de proveedores
    providers_list = list(PROVIDERS.keys())
    
    print("Proveedores disponibles:")
    for i, provider in enumerate(providers_list, 1):
        models = ", ".join(PROVIDERS[provider]["models_hint"][:2])
        print(f"  {i}. {provider} (ej: {models})")
    
    print("\n0. Probar todos los proveedores")
    print("-1. Salir")
    
    choice = input("\nSelecciona un proveedor (número): ").strip()
    
    if choice == "-1":
        print("👋 ¡Hasta luego!")
        return
    
    if choice == "0":
        # Probar todos
        results = {}
        for provider in providers_list:
            api_key = input(f"\nAPI Key para {provider} (Enter para saltar): ").strip()
            if not api_key:
                print(f"⏭️  Saltando {provider}")
                continue
            
            model_custom = input(f"Modelo para {provider} (Enter para default: {PROVIDERS[provider]['models_hint'][0]}): ").strip()
            model = model_custom if model_custom else PROVIDERS[provider]["models_hint"][0]
            
            results[provider] = test_provider(provider, api_key, model)
        
        # Resumen
        print(f"\n{'='*60}")
        print("RESUMEN DE PRUEBAS")
        print(f"{'='*60}")
        for provider, success in results.items():
            status = "✅ OK" if success else "❌ ERROR"
            print(f"{status} - {provider}")
    else:
        # Probar uno específico
        try:
            idx = int(choice) - 1
            if idx < 0 or idx >= len(providers_list):
                print("❌ Selección inválida")
                return
            
            provider = providers_list[idx]
            api_key = input(f"API Key para {provider}: ").strip()
            
            if not api_key:
                print("❌ API Key requerida")
                return
            
            model_custom = input(f"Modelo (Enter para default: {PROVIDERS[provider]['models_hint'][0]}): ").strip()
            model = model_custom if model_custom else PROVIDERS[provider]["models_hint"][0]
            
            test_provider(provider, api_key, model)
            
        except ValueError:
            print("❌ Entrada inválida")
            return
    
    print(f"\n{'='*60}")
    print("Prueba completada.")
    print(f"{'='*60}\n")


if __name__ == "__main__":
    main()
