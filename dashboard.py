import streamlit as st
import pandas as pd
import psycopg2
import os

st.set_page_config(page_title="Monitor Dentalink", layout="wide")

# Conexión a Postgres
conn = psycopg2.connect(os.getenv("DATABASE_URL"))

st.title("📊 Monitor de Webhooks Dentalink")

# Consulta con filtros
df = pd.read_sql("SELECT fecha_recepcion, evento_tipo, paciente_nombre FROM webhooks_dentalink ORDER BY fecha_recepcion DESC", conn)

# Sidebar para categorización
st.sidebar.header("Filtros")
filtro_tipo = st.sidebar.multiselect("Tipo de Evento", options=df["evento_tipo"].unique())

if filtro_tipo:
    df = df[df["evento_tipo"].isin(filtro_tipo)]

st.table(df)