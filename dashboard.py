import streamlit as st
import pandas as pd
import json
import time
import os
from PIL import Image

st.set_page_config(
    page_title="Monitor de Vida Interior",
    page_icon="🌍",
    layout="wide",
)

st.title("🌍 Monitor de Vida Interior")

# Función para cargar datos
def cargar_datos():
    if os.path.exists("historia_mundo.json"):
        try:
            with open("historia_mundo.json", "r") as f:
                data = json.load(f)
                if data:
                    return data[-1] # Último registro
        except:
            pass
    return None

# Layout
col_visual, col_datos = st.columns([2, 1])

with col_visual:
    st.subheader("👁️ Vista del Mundo")
    
    # Contenedor para la imagen
    img_container = st.empty()
    
    if os.path.exists("estado_visual.png"):
        # Usamos PIL para abrir y mostrar, evitando cache agresivo de streamlit
        try:
            image = Image.open("estado_visual.png")
            img_container.image(image, caption="Estado Actual", use_container_width=True)
        except Exception as e:
            st.error(f"Error al cargar imagen: {e}")
    else:
        st.warning("Esperando snapshot del servidor...")

with col_datos:
    st.subheader("📊 Métricas en Tiempo Real")
    
    metrics_container = st.empty()
    
    ultimo_dato = cargar_datos()
    
    if ultimo_dato:
        st.metric("Día", ultimo_dato.get("dia", "?"))
        st.metric("Población", ultimo_dato.get("poblacion", "?"))
        
        recursos = ultimo_dato.get("recursos", {})
        c1, c2, c3 = st.columns(3)
        c1.metric("Madera", recursos.get("madera", 0))
        c2.metric("Piedra", recursos.get("piedra", 0))
        c3.metric("Comida", recursos.get("comida", 0))
        
        st.divider()
        st.write("🛠️ **Tecnologías:**")
        techs = ultimo_dato.get("tecnologias", [])
        if techs:
            for t in techs:
                st.write(f"- {t}")
        else:
            st.write("_Ninguna descubierta aún_")
            
    else:
        st.info("Esperando datos de la simulación...")

# Botón de refresco manual
if st.button("🔄 Actualizar Ahora"):
    st.rerun()

# Auto-refresh (opcional, consumo de recursos)
# time.sleep(2)
# st.rerun()
