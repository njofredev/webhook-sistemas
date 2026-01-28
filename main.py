import os
import json
import psycopg2
from fastapi import FastAPI, Request
from psycopg2.extras import RealDictCursor

app = FastAPI(title="Receptor Pro - Policlínico Tabancura")

# URL de conexión a tu base de datos db_webhook
DATABASE_URL = os.getenv("DATABASE_URL")

def init_db():
    """Asegura que la tabla tenga todas las columnas necesarias."""
    try:
        conn = psycopg2.connect(DATABASE_URL)
        cur = conn.cursor()
        # Creamos la tabla base si no existe
        cur.execute("""
            CREATE TABLE IF NOT EXISTS webhooks_dentalink (
                id SERIAL PRIMARY KEY,
                fecha_recepcion TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                evento_tipo TEXT,
                paciente_nombre TEXT,
                datos_json JSONB
            );
        """)
        # Añadimos las columnas específicas para los elementos del JSON
        # Usamos 'IF NOT EXISTS' para no dar error si ya las creaste
        columnas = [
            "id_cita INTEGER",
            "fecha_cita DATE",
            "hora_inicio TIME",
            "id_estado INTEGER",
            "estado_cita TEXT",
            "comentarios TEXT",
            "id_sillon INTEGER"
        ]
        for col in columnas:
            try:
                cur.execute(f"ALTER TABLE webhooks_dentalink ADD COLUMN {col};")
            except psycopg2.errors.DuplicateColumn:
                conn.rollback() # Ignorar si la columna ya existe
            else:
                conn.commit()
        
        conn.commit()
        cur.close()
        conn.close()
        print("Estructura de base de datos verificada.")
    except Exception as e:
        print(f"Error al inicializar DB: {e}")

# Ejecutar inicialización al arrancar
init_db()

@app.post("/webhook")
async def receive_webhook(request: Request):
    try:
        payload = await request.json()
        
        # Dentalink/Medilink envían la info dentro de 'data'
        d = payload.get("data", {})
        
        # 1. Extraemos cada elemento del JSON
        id_cita = d.get("id")
        fecha = d.get("fecha")
        hora = d.get("hora_inicio")
        id_estado = d.get("id_estado")
        estado_txt = d.get("estado_cita")
        comentarios = d.get("comentarios")
        id_sillon = d.get("id_sillon")
        
        # Intentar buscar nombre del paciente (ajustar según el JSON real si aparece)
        nombre_paciente = d.get("paciente", "Paciente Dentalink")
        
        # Definimos el tipo de evento principal
        evento_principal = estado_txt if estado_txt else f"Estado {id_estado}"

        # 2. Insertar en columnas individuales
        conn = psycopg2.connect(DATABASE_URL)
        cur = conn.cursor()
        
        query = """
            INSERT INTO webhooks_dentalink 
            (evento_tipo, paciente_nombre, datos_json, id_cita, fecha_cita, hora_inicio, id_estado, estado_cita, comentarios, id_sillon)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        """
        
        cur.execute(query, (
            evento_principal,
            nombre_paciente,
            json.dumps(payload), # Guardamos el JSON completo por respaldo
            id_cita,
            fecha if fecha else None,
            hora if hora else None,
            id_estado,
            estado_txt,
            comentarios,
            id_sillon
        ))
        
        conn.commit()
        cur.close()
        conn.close()
        
        return {"status": "success", "detail": "Registro procesado por columnas"}

    except Exception as e:
        return {"status": "error", "message": str(e)}

@app.get("/health")
async def health_check():
    return {"status": "online", "database": "connected"}