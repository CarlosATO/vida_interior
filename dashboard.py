import streamlit as st
import pandas as pd
import json
import time
import os

st.set_page_config(page_title="Dashboard Vida Interior", layout="wide")

st.title("🌍 Dashboard de Vida Interior")

ARCHIVO_HISTORIA = "historia_mundo.json"

def cargar_datos():
    if not os.path.exists(ARCHIVO_HISTORIA):
        return None
    
    with open(ARCHIVO_HISTORIA, "r") as f:
        try:
            data = json.load(f)
            return data
        except json.JSONDecodeError:
            return None

placeholder = st.empty()

while True:
    data = cargar_datos()
    
    with placeholder.container():
        if not data:
            st.warning("⏳ Esperando datos de la simulación...")
        else:
            # Stats Generales (Último registro)
            ultimo = data[-1]
            col1, col2, col3, col4 = st.columns(4)
            
            col1.metric("Día", ultimo["dia"])
            col2.metric("Población", ultimo["poblacion"])
            col3.metric("Felicidad", f"{ultimo['felicidad_promedio']}%")
            col4.metric("Tecnologías", len(ultimo["tecnologias"]))
            
            # --- GRÁFICOS ---
            st.markdown("### 📈 Evolución")
            
            # Preparar DataFrame
            df = pd.DataFrame(data)
            
            # Gráfico 1: Población y Recursos
            chart_data = pd.DataFrame()
            chart_data["Día"] = df["dia"]
            chart_data["Población"] = df["poblacion"]
            
            # Extraer recursos de forma segura
            recursos_list = [d["recursos"] for d in data]
            df_recursos = pd.DataFrame(recursos_list)
            
            chart_data = pd.concat([chart_data, df_recursos], axis=1)
            chart_data = chart_data.set_index("Día")
            
            st.line_chart(chart_data)
            
            # --- TECNOLOGÍAS Y HÉROES ---
            col_tech, col_heroes = st.columns(2)
            
            with col_tech:
                st.markdown("### 🧪 Tecnologías Descubiertas")
                if ultimo["tecnologias"]:
                    st.write(", ".join(ultimo["tecnologias"]))
                else:
                    st.info("Aún en la Edad de Piedra...")
            
            with col_heroes:
                st.markdown("### 🦸‍♀️ Héroes de la Civilización")
                heroes = ultimo["heroes"] # Lista de dicts
                if heroes:
                    df_heroes = pd.DataFrame(heroes)
                    # Formatear inventos a string
                    df_heroes["inventos"] = df_heroes["inventos"].apply(lambda x: ", ".join(x))
                    st.dataframe(df_heroes)
                else:
                    st.info("Aún no hay héroes.")

    time.sleep(2)
