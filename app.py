"""
Punto de entrada principal de la aplicación.

Este es un wrapper para mantener compatibilidad. 
La aplicación se ha modularizado en:
- config/: Configuración central
- models/: Modelos de datos
- utils/: Utilidades de texto y DOCX
- core/: Lógica de negocio principal
- ai/: Proveedores y prompts de IA
- ui/: Interfaz de usuario con Streamlit

Para ejecutar la aplicación: streamlit run app.py
"""

from ui.streamlit_app import main

if __name__ == "__main__":
    main()
