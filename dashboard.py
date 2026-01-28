import streamlit as st
import pandas as pd
import psycopg2
from psycopg2.extras import RealDictCursor
import os
import plotly.express as px

# Configuración de página
st.set_page_config(page_title="Dashboard Webhooks - Tabancura", layout="wide")

# Conexión a la base de datos db_webhook
DATABASE_URL = os.getenv("DATABASE_URL")

def get_data():
    try:
        conn = psycopg2.connect(DATABASE_URL)
        # Traemos todas las columnas individuales que creamos
        query = """
            SELECT 
                fecha_recepcion, 
                evento_tipo, 
                paciente_nombre, 
                id_cita, 
                fecha_cita, 
                hora_inicio, 
                estado_cita, 
                id_sillon,
                comentarios
            FROM webhooks_dentalink 
            ORDER BY fecha_recepcion DESC
        """
        df = pd.read_sql(query, conn)
        conn.close()
        return df
    except Exception as e:
        st.error(f"Error de conexión: {e}")
        return pd.DataFrame()

# Título e interfaz
st.title("🏥 Monitor de Citas Dentalink/Medilink")
st.markdown("Visualización en tiempo real de los webhooks recibidos para el Policlínico Tabancura.")

df = get_data()

if not df.empty:
    # --- BARRA LATERAL (FILTROS) ---
    st.sidebar.header("Filtros")
    
    # Filtro por Estado
    estados = df['evento_tipo'].unique().tolist()
    filtro_estado = st.sidebar.multiselect("Categoría de Cita:", estados, default=estados)
    
    # Filtro por Sillón
    sillones = [s for s in df['id_sillon'].unique() if s is not None]
    filtro_sillon = st.sidebar.multiselect("Filtrar por Sillón:", sillones)

    # Búsqueda por Paciente
    buscar_paciente = st.sidebar.text_input("Buscar por nombre de paciente:")

    # Aplicar Filtros
    df_filtrado = df[df['evento_tipo'].isin(filtro_estado)]
    if filtro_sillon:
        df_filtrado = df_filtrado[df_filtrado['id_sillon'].isin(filtro_sillon)]
    if buscar_paciente:
        df_filtrado = df_filtrado[df_filtrado['paciente_nombre'].str.contains(buscar_paciente, case=False)]

    # --- MÉTRICAS ---
    m1, m2, m3, m4 = st.columns(4)
    m1.metric("Total Webhooks", len(df_filtrado))
    m2.metric("Citas Hoy", len(df_filtrado[pd.to_datetime(df_filtrado['fecha_cita']).dt.date == pd.Timestamp.now().date()]))
    m3.metric("Pacientes Únicos", df_filtrado['paciente_nombre'].nunique())
    m4.metric("Sillones Activos", df_filtrado['id_sillon'].nunique())

    # --- GRÁFICOS ---
    col_izq, col_der = st.columns(2)
    
    with col_izq:
        st.subheader("Distribución por Estado")
        fig_estado = px.pie(df_filtrado, names='evento_tipo', hole=0.4, color_discrete_sequence=px.colors.qualitative.Safe)
        st.plotly_chart(fig_estado, use_container_width=True)

    with col_der:
        st.subheader("Citas por Sillón")
        if not df_filtrado['id_sillon'].isnull().all():
            fig_sillon = px.bar(df_filtrado['id_sillon'].value_counts().reset_index(), x='id_sillon', y='count', labels={'count':'Cantidad', 'id_sillon':'Sillón ID'})
            st.plotly_chart(fig_sillon, use_container_width=True)
        else:
            st.info("No hay datos de sillones disponibles para graficar.")

    # --- TABLA DE DATOS ---
    st.subheader("Detalle de Registros")
    st.dataframe(df_filtrado, use_container_width=True, hide_index=True)

else:
    st.warning("No se encontraron datos en la base de datos `db_webhook`. Asegúrate de que el receptor esté funcionando.")

# Botón de actualización
if st.button('🔄 Actualizar Datos'):
    st.rerun()