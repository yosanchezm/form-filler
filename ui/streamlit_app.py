"""
Interfaz de usuario con Streamlit.
"""

import os

import streamlit as st
import requests
import json

from config.settings import DEFAULT_KB_DIR, DEFAULT_OUT_DIR
from core.knowledge_base import load_kb_from_xlsx_bytes, load_kb_from_xlsx_path
from core.processor import run_mvp2
from ai.providers import PROVIDERS


def main():
    """Función principal de la aplicación Streamlit."""
    st.set_page_config(page_title="Rellenador DOCX (MVP2)", layout="wide")
    st.title("Rellenador de formularios DOCX (MVP 2) — reglas + IA (local)")

    # Sidebar: AI settings
    st.sidebar.header("IA (opcional)")

    use_ai = st.sidebar.toggle("Usar IA para completar lo que falte", value=False)

    provider = st.sidebar.selectbox("Proveedor", list(PROVIDERS.keys()), index=0)
    models_hint = PROVIDERS[provider]["models_hint"]
    model = st.sidebar.text_input("Modelo", value=models_hint[0] if models_hint else "")

    api_key = st.sidebar.text_input(
        "API Key",
        type="password",
        help="Se usa solo localmente en tu PC. No se guarda en disco."
    )

    confidence_threshold = st.sidebar.slider(
        "Umbral de confianza para aplicar",
        min_value=0.0,
        max_value=1.0,
        value=0.75,
        step=0.05
    )
    temperature = st.sidebar.slider(
        "Temperatura",
        min_value=0.0,
        max_value=1.0,
        value=0.0,
        step=0.1
    )

    st.sidebar.caption("Tip: para MVP2 usa temp=0.0 y threshold ~0.75 para estabilidad.")

    col1, col2 = st.columns(2)

    with col1:
        st.subheader("1) Sube tu formulario (.docx)")
        docx_file = st.file_uploader("Documento DOCX", type=["docx"])

    with col2:
        st.subheader("2) Selecciona o sube la base de conocimiento (.xlsx)")
        os.makedirs(DEFAULT_KB_DIR, exist_ok=True)
        kb_files = [f for f in os.listdir(DEFAULT_KB_DIR) if f.lower().endswith(".xlsx")]
        kb_choice = st.selectbox(
            "Bases disponibles (carpeta /knowledge)",
            ["(subir manualmente)"] + kb_files
        )

        kb_upload = None
        if kb_choice == "(subir manualmente)":
            kb_upload = st.file_uploader("Sube XLSX (Atributo/Valor)", type=["xlsx"])

    st.divider()

    # Botones de acción
    col_run, col_clear = st.columns([3, 1])
    with col_run:
        run = st.button("Generar DOCX de salida", type="primary", disabled=(docx_file is None), use_container_width=True)
    with col_clear:
        if st.button("🗑️ Limpiar resultados", use_container_width=True):
            # Limpiar el session_state
            for key in ['out_bytes', 'base_name', 'filled_rules', 'filled_ai', 'skipped_ai', 'out_path']:
                if key in st.session_state:
                    del st.session_state[key]
            st.rerun()

    if run:
        try:
            if use_ai:
                if not api_key.strip():
                    st.error("Activaste IA pero no ingresaste API Key.")
                    st.stop()
                if not model.strip():
                    st.error("Modelo vacío.")
                    st.stop()

            # KB
            if kb_choice != "(subir manualmente)":
                kb = load_kb_from_xlsx_path(os.path.join(DEFAULT_KB_DIR, kb_choice))
            else:
                if kb_upload is None:
                    st.error("Debes seleccionar una base desde /knowledge o subir un XLSX.")
                    st.stop()
                kb = load_kb_from_xlsx_bytes(kb_upload.getvalue())

            # Process
            out_bytes, filled_rules, filled_ai, skipped_ai = run_mvp2(
                docx_bytes=docx_file.getvalue(),
                kb=kb,
                use_ai=use_ai,
                provider=provider,
                api_key=api_key.strip(),
                model=model.strip(),
                confidence_threshold=confidence_threshold,
                temperature=temperature,
            )

            # Save output
            os.makedirs(DEFAULT_OUT_DIR, exist_ok=True)
            base_name = os.path.splitext(docx_file.name)[0]
            out_path = os.path.join(DEFAULT_OUT_DIR, f"{base_name}__output.docx")
            with open(out_path, "wb") as f:
                f.write(out_bytes)

            # Guardar resultados en session_state para que persistan
            st.session_state.out_bytes = out_bytes
            st.session_state.base_name = base_name
            st.session_state.filled_rules = filled_rules
            st.session_state.filled_ai = filled_ai
            st.session_state.skipped_ai = skipped_ai
            st.session_state.out_path = out_path

        except requests.HTTPError as e:
            st.error("Error HTTP llamando al proveedor de IA.")
            st.exception(e)
            if e.response is not None:
                st.code(e.response.text)
        except json.JSONDecodeError as e:
            st.error("❌ La IA no devolvió JSON puro. Baja temperatura a 0.0 o cambia el modelo.")
            st.error(f"**Error específico:** {str(e)}")
            st.info("💡 **Sugerencias:**\n- Intenta con temperatura = 0.0\n- Cambia a otro modelo (ej. gpt-4o-mini si usas OpenAI)\n- Revisa que la API key sea correcta")
            st.stop()
        except ValueError as e:
            # Captura los ValueError que lanzamos desde providers.py con detalles de la respuesta
            if "devolvió texto no-JSON" in str(e) or "no devolvió candidatos" in str(e):
                st.error("❌ Error al procesar la respuesta de la IA")
                st.error(str(e))
                st.info("💡 **Sugerencias:**\n- Intenta con temperatura = 0.0\n- Cambia a otro modelo\n- Si usas Gemini, asegúrate de que el modelo esté disponible")
            else:
                st.error("Error de validación:")
                st.exception(e)
            st.stop()
        except Exception as e:
            st.exception(e)

    # Mostrar resultados si existen en session_state
    if 'out_bytes' in st.session_state:
        st.success(f"✅ Listo. Guardado automáticamente en: {st.session_state.out_path}")

        st.download_button(
            label="📥 Descargar output.docx",
            data=st.session_state.out_bytes,
            file_name=f"{st.session_state.base_name}__output.docx",
            mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            use_container_width=True
        )

        # Reportes
        c1, c2, c3 = st.columns(3)
        with c1:
            st.subheader(f"Rellenado por reglas: {len(st.session_state.filled_rules)}")
            st.dataframe(
                [{"donde": e.where, "label": e.label, "valor": e.value} for e in st.session_state.filled_rules],
                use_container_width=True
            )
        with c2:
            st.subheader(f"Rellenado por IA: {len(st.session_state.filled_ai)}")
            st.dataframe(
                [{"donde": e.where, "label": e.label, "valor": e.value, "conf": e.confidence} for e in st.session_state.filled_ai],
                use_container_width=True
            )
        with c3:
            st.subheader(f"Pendiente / revisión: {len(st.session_state.skipped_ai)}")
            st.dataframe(
                st.session_state.skipped_ai,
                use_container_width=True
            )

    st.caption("MVP2: placeholders [..] + underscores + tablas. IA solo propone valores; el motor aplica cambios determinísticamente.")


if __name__ == "__main__":
    main()
