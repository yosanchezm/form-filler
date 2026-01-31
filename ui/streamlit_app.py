"""
Interfaz de usuario con Streamlit - Versión mejorada.
"""

import os

import streamlit as st
import requests
import json

from config.settings import DEFAULT_KB_DIR, DEFAULT_OUT_DIR
from core.knowledge_base import load_kb_from_xlsx_bytes, load_kb_from_xlsx_path, get_kb_summary, SEMANTIC_SEARCH_AVAILABLE
from core.processor import run_mvp2, analyze_document, run_rules_only, get_ai_availability
from ai.providers import PROVIDERS

# Intentar importar LangChain providers
try:
    from ai.langchain_processor import LANGCHAIN_PROVIDERS, get_provider_models
    LANGCHAIN_AVAILABLE = True
except ImportError:
    LANGCHAIN_AVAILABLE = False
    LANGCHAIN_PROVIDERS = {}


def main():
    """Función principal de la aplicación Streamlit."""
    st.set_page_config(
        page_title="Form Filler Pro", 
        layout="wide",
        page_icon="📝"
    )
    
    # Header
    st.title("📝 Form Filler Pro")
    st.caption("Rellenador inteligente de formularios DOCX con IA")
    
    # Mostrar estado del sistema
    _show_system_status()

    # Sidebar: Configuración
    _setup_sidebar()

    # Área principal
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("1️⃣ Documento DOCX")
        docx_file = st.file_uploader(
            "Sube tu formulario",
            type=["docx"],
            help="Documento Word con campos a rellenar"
        )
        
        # Preview del documento si está cargado
        if docx_file:
            _show_document_preview(docx_file)

    with col2:
        st.subheader("2️⃣ Base de Conocimiento")
        kb, kb_source = _load_knowledge_base()
        
        if kb:
            _show_kb_summary(kb, kb_source)

    st.divider()

    # Opciones avanzadas
    with st.expander("⚙️ Opciones avanzadas", expanded=False):
        col_opt1, col_opt2 = st.columns(2)
        
        with col_opt1:
            use_semantic = st.checkbox(
                "🔍 Búsqueda semántica en KB",
                value=SEMANTIC_SEARCH_AVAILABLE,
                disabled=not SEMANTIC_SEARCH_AVAILABLE,
                help="Usa embeddings para encontrar matches aunque las palabras no coincidan exactamente"
            )
            
            use_langchain = st.checkbox(
                "🦜 Usar LangChain",
                value=LANGCHAIN_AVAILABLE,
                disabled=not LANGCHAIN_AVAILABLE,
                help="Framework avanzado para IA con output estructurado y retry automático"
            )
        
        with col_opt2:
            preview_only = st.checkbox(
                "👁️ Solo preview (sin IA)",
                value=False,
                help="Procesa solo con reglas para ver qué se puede llenar automáticamente"
            )

    # Botones de acción
    _action_buttons(docx_file, kb, use_semantic, use_langchain, preview_only)
    
    # Mostrar resultados
    _show_results()

    # Footer
    st.divider()
    st.caption("Form Filler Pro v2.0 - Reglas + IA + LangChain + Búsqueda Semántica")


def _show_system_status():
    """Muestra el estado del sistema en una barra compacta."""
    ai_info = get_ai_availability()
    
    cols = st.columns(4)
    with cols[0]:
        status = "✅" if ai_info["langchain_available"] else "❌"
        st.metric("LangChain", status)
    with cols[1]:
        status = "✅" if SEMANTIC_SEARCH_AVAILABLE else "❌"
        st.metric("Búsqueda Semántica", status)
    with cols[2]:
        st.metric("Proveedores IA", len(PROVIDERS))
    with cols[3]:
        if ai_info["langchain_available"]:
            st.metric("LangChain Providers", len(ai_info["langchain_providers"]))


def _setup_sidebar():
    """Configura el sidebar con opciones de IA."""
    st.sidebar.header("🤖 Configuración de IA")

    use_ai = st.sidebar.toggle(
        "Usar IA para completar",
        value=False,
        help="Activa la IA para campos que no se pueden resolver con reglas"
    )
    
    # Guardar en session_state
    st.session_state.use_ai = use_ai

    if use_ai:
        # Selector de proveedor
        all_providers = list(PROVIDERS.keys())
        provider = st.sidebar.selectbox(
            "Proveedor",
            all_providers,
            index=0,
            help="Selecciona el servicio de IA a usar"
        )
        st.session_state.provider = provider
        
        # Selector de modelo
        if LANGCHAIN_AVAILABLE and provider in LANGCHAIN_PROVIDERS:
            models_hint = get_provider_models(provider)
            badge = "🦜 LangChain"
        else:
            models_hint = PROVIDERS[provider].get("models_hint", [])
            badge = "📡 API directa"
        
        st.sidebar.caption(f"Modo: {badge}")
        
        model = st.sidebar.text_input(
            "Modelo",
            value=models_hint[0] if models_hint else "",
            help=f"Modelos sugeridos: {', '.join(models_hint[:3])}"
        )
        st.session_state.model = model

        # API Key
        api_key = st.sidebar.text_input(
            "API Key",
            type="password",
            help="Tu clave API. Se usa solo localmente, no se guarda."
        )
        st.session_state.api_key = api_key

        # Parámetros avanzados
        with st.sidebar.expander("Parámetros avanzados"):
            confidence_threshold = st.slider(
                "Umbral de confianza",
                min_value=0.0,
                max_value=1.0,
                value=0.7,
                step=0.05,
                help="Solo aplica valores con confianza mayor a este umbral"
            )
            st.session_state.confidence_threshold = confidence_threshold
            
            temperature = st.slider(
                "Temperatura",
                min_value=0.0,
                max_value=1.0,
                value=0.0,
                step=0.1,
                help="0.0 = determinista, 1.0 = más creativo"
            )
            st.session_state.temperature = temperature
    else:
        # Valores por defecto cuando IA está desactivada
        st.session_state.provider = list(PROVIDERS.keys())[0]
        st.session_state.model = ""
        st.session_state.api_key = ""
        st.session_state.confidence_threshold = 0.7
        st.session_state.temperature = 0.0


def _load_knowledge_base():
    """Carga la base de conocimiento."""
    os.makedirs(DEFAULT_KB_DIR, exist_ok=True)
    kb_files = [f for f in os.listdir(DEFAULT_KB_DIR) if f.lower().endswith(".xlsx")]
    
    kb_choice = st.selectbox(
        "Selecciona una base de conocimiento",
        ["(subir archivo)"] + kb_files,
        help="Bases disponibles en /knowledge o sube una nueva"
    )

    kb = None
    kb_source = None
    
    if kb_choice == "(subir archivo)":
        kb_upload = st.file_uploader(
            "Sube archivo Excel",
            type=["xlsx"],
            help="Excel con columnas 'Atributo' y 'Valor'"
        )
        if kb_upload:
            try:
                kb = load_kb_from_xlsx_bytes(kb_upload.getvalue())
                kb_source = kb_upload.name
            except Exception as e:
                st.error(f"Error cargando KB: {e}")
    else:
        try:
            kb = load_kb_from_xlsx_path(os.path.join(DEFAULT_KB_DIR, kb_choice))
            kb_source = kb_choice
        except Exception as e:
            st.error(f"Error cargando KB: {e}")
    
    return kb, kb_source


def _show_kb_summary(kb, kb_source):
    """Muestra resumen de la base de conocimiento."""
    summary = get_kb_summary(kb)
    
    st.success(f"✅ KB cargada: **{kb_source}**")
    
    col1, col2 = st.columns(2)
    with col1:
        st.metric("Entradas", summary["total_entries"])
    with col2:
        embed_status = "✅" if summary["has_embeddings"] else "❌"
        st.metric("Embeddings", embed_status)
    
    with st.expander("Ver atributos disponibles"):
        for attr in summary["attributes"][:20]:
            st.write(f"• {attr}")
        if len(summary["attributes"]) > 20:
            st.caption(f"... y {len(summary['attributes']) - 20} más")


def _show_document_preview(docx_file):
    """Muestra preview y análisis del documento."""
    try:
        analysis = analyze_document(docx_file.getvalue())
        counts = analysis["counts"]
        
        st.success(f"✅ Documento cargado: **{docx_file.name}**")
        
        # Métricas de campos
        cols = st.columns(5)
        with cols[0]:
            st.metric("Brackets [...]", counts["brackets"])
        with cols[1]:
            st.metric("Underscores ___", counts["underscores"])
        with cols[2]:
            st.metric("Celdas tabla", counts["table_cells"])
        with cols[3]:
            st.metric("Formateados", counts.get("formatted", 0))
        with cols[4]:
            st.metric("Total campos", counts["total"])
        
        # Detalles expandibles
        with st.expander("📋 Ver tokens bracket [...]", expanded=False):
            if analysis.get("bracket_tokens"):
                for tok in analysis["bracket_tokens"]:
                    st.code(tok, language=None)
            else:
                st.info("No se encontraron tokens bracket")
        
        with st.expander("📅 Ver campos de fecha", expanded=False):
            if analysis.get("date_fields"):
                for df in analysis["date_fields"]:
                    st.write(f"📍 **{df['where']}**")
                    st.caption(df['sample'])
            else:
                st.info("No se detectaron campos de fecha")
        
        with st.expander("🎨 Ver campos formateados (negrita, sombreado, etc)", expanded=False):
            if analysis.get("formatted_fields"):
                for ff in analysis["formatted_fields"]:
                    format_tags = " ".join([f"`{f}`" for f in ff['format']])
                    st.write(f"📍 **{ff['where']}** {format_tags}")
                    st.caption(ff['text'])
            else:
                st.info("No se detectaron campos con formato especial")
        
        # Info adicional
        with st.expander("ℹ️ Más información"):
            st.write(f"**Tablas:** {analysis.get('total_tables', 0)}")
            st.write(f"**Párrafos:** {analysis.get('total_paragraphs', 0)}")
            st.write(f"**Checkboxes:** {counts.get('checkboxes', 0)}")
                    
    except Exception as e:
        st.error(f"Error analizando documento: {e}")


def _action_buttons(docx_file, kb, use_semantic, use_langchain, preview_only):
    """Muestra botones de acción."""
    col_run, col_preview, col_clear = st.columns([2, 1, 1])
    
    with col_run:
        run_disabled = docx_file is None or kb is None
        run_label = "🚀 Procesar documento" if not preview_only else "👁️ Preview (solo reglas)"
        
        if st.button(run_label, type="primary", disabled=run_disabled, use_container_width=True):
            _process_document(docx_file, kb, use_semantic, use_langchain, preview_only)
    
    with col_preview:
        if st.button("📊 Analizar", disabled=docx_file is None, use_container_width=True):
            if docx_file:
                _show_document_preview(docx_file)
    
    with col_clear:
        if st.button("🗑️ Limpiar", use_container_width=True):
            _clear_results()
            st.rerun()


def _process_document(docx_file, kb, use_semantic, use_langchain, preview_only):
    """Procesa el documento."""
    use_ai = st.session_state.get("use_ai", False) and not preview_only
    
    try:
        # Validaciones
        if use_ai:
            api_key = st.session_state.get("api_key", "").strip()
            model = st.session_state.get("model", "").strip()
            
            if not api_key:
                st.error("❌ API Key requerida para usar IA")
                return
            if not model:
                st.error("❌ Modelo requerido")
                return
        
        with st.spinner("Procesando documento..." if use_ai else "Aplicando reglas..."):
            if preview_only or not use_ai:
                # Solo reglas
                out_bytes, filled, pending = run_rules_only(
                    docx_bytes=docx_file.getvalue(),
                    kb=kb,
                    use_semantic_search=use_semantic
                )
                filled_ai = []
                skipped = pending  # Los pendientes se muestran como "para revisar"
            else:
                # Procesamiento completo con IA
                out_bytes, filled, filled_ai, skipped = run_mvp2(
                    docx_bytes=docx_file.getvalue(),
                    kb=kb,
                    use_ai=True,
                    provider=st.session_state.provider,
                    api_key=st.session_state.api_key,
                    model=st.session_state.model,
                    confidence_threshold=st.session_state.confidence_threshold,
                    temperature=st.session_state.temperature,
                    use_langchain=use_langchain,
                    use_semantic_search=use_semantic
                )
        
        # Guardar output
        os.makedirs(DEFAULT_OUT_DIR, exist_ok=True)
        base_name = os.path.splitext(docx_file.name)[0]
        out_path = os.path.join(DEFAULT_OUT_DIR, f"{base_name}__output.docx")
        
        with open(out_path, "wb") as f:
            f.write(out_bytes)
        
        # Guardar en session_state
        st.session_state.out_bytes = out_bytes
        st.session_state.base_name = base_name
        st.session_state.filled_rules = filled
        st.session_state.filled_ai = filled_ai
        st.session_state.skipped = skipped
        st.session_state.out_path = out_path
        st.session_state.preview_only = preview_only
        
        st.rerun()
        
    except requests.HTTPError as e:
        st.error("❌ Error de conexión con el proveedor de IA")
        if e.response is not None:
            st.code(e.response.text[:500])
    except json.JSONDecodeError as e:
        st.error("❌ La IA no devolvió JSON válido")
        st.info("💡 Intenta con temperatura = 0.0 o cambia de modelo")
    except ValueError as e:
        st.error(f"❌ Error: {e}")
    except Exception as e:
        st.exception(e)


def _show_results():
    """Muestra los resultados del procesamiento."""
    if 'out_bytes' not in st.session_state:
        return
    
    preview_only = st.session_state.get('preview_only', False)
    
    # Banner de éxito
    if preview_only:
        st.info(f"👁️ Preview completado. Archivo guardado en: `{st.session_state.out_path}`")
    else:
        st.success(f"✅ ¡Documento procesado! Guardado en: `{st.session_state.out_path}`")
    
    # Botón de descarga
    st.download_button(
        label="📥 Descargar documento procesado",
        data=st.session_state.out_bytes,
        file_name=f"{st.session_state.base_name}__output.docx",
        mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        use_container_width=True
    )

    # Métricas resumen
    filled_rules = st.session_state.get('filled_rules', [])
    filled_ai = st.session_state.get('filled_ai', [])
    skipped = st.session_state.get('skipped', [])
    
    cols = st.columns(4)
    with cols[0]:
        st.metric("✅ Por reglas", len(filled_rules))
    with cols[1]:
        st.metric("🤖 Por IA", len(filled_ai))
    with cols[2]:
        st.metric("⚠️ Pendientes", len(skipped))
    with cols[3]:
        total = len(filled_rules) + len(filled_ai)
        st.metric("📊 Total llenados", total)

    # Tablas de detalles
    tabs = st.tabs(["📋 Por Reglas", "🤖 Por IA", "⚠️ Pendientes"])
    
    with tabs[0]:
        if filled_rules:
            st.dataframe(
                [{"Ubicación": e.where, "Campo": e.label, "Valor": e.value, "Confianza": e.confidence} 
                 for e in filled_rules],
                use_container_width=True
            )
        else:
            st.info("No se llenaron campos por reglas")
    
    with tabs[1]:
        if filled_ai:
            st.dataframe(
                [{"Ubicación": e.where, "Campo": e.label, "Valor": e.value, "Confianza": f"{e.confidence:.0%}"} 
                 for e in filled_ai],
                use_container_width=True
            )
        else:
            st.info("No se usó IA o no llenó campos adicionales")
    
    with tabs[2]:
        if skipped:
            st.dataframe(skipped, use_container_width=True)
        else:
            st.success("¡Todos los campos fueron llenados!")


def _clear_results():
    """Limpia los resultados del session_state."""
    keys_to_clear = [
        'out_bytes', 'base_name', 'filled_rules', 'filled_ai', 
        'skipped', 'out_path', 'preview_only'
    ]
    for key in keys_to_clear:
        if key in st.session_state:
            del st.session_state[key]


if __name__ == "__main__":
    main()

