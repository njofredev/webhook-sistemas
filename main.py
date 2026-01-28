import os
import json
import psycopg2
from fastapi import FastAPI, Request, HTTPException
from psycopg2.extras import RealDictCursor

app = FastAPI(title="Webhook Receiver - Policlínico Tabancura")

# 1. Configuración de la Base de Datos
# Asegúrate de que esta variable esté en las 'Environment Variables' de Coolify
DATABASE_URL = os.getenv("DATABASE_URL")

def init_db():
    """Crea la tabla si no existe al iniciar la aplicación."""
    try:
        conn = psycopg2.connect(DATABASE_URL)
        cur = conn.cursor()
        cur.execute("""
            CREATE TABLE IF NOT EXISTS webhooks_dentalink (
                id SERIAL PRIMARY KEY,
                fecha_recepcion TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                evento_tipo TEXT,
                paciente_nombre TEXT,
                datos_json JSONB
            );
        """)
        conn.commit()
        cur.close()
        conn.close()
        print("Base de datos inicializada correctamente.")
    except Exception as e:
        print(f"Error inicializando la base de datos: {e}")

# Inicializar al cargar el script
init_db()

@app.get("/")
async def root():
    return {"message": "Webhook Listener activo para Policlínico Tabancura"}

@app.post("/webhook")
async def receive_webhook(request: Request):
    try:
        # 2. Recibir y procesar el JSON
        payload = await request.json()
        
        # Extraer datos según la estructura de Dentalink/Medilink
        # Ajustamos los nombres de las llaves según tus pruebas previas
        evento = payload.get("nombre_evento") or payload.get("evento") or "desconocido"
        
        # Intentar extraer el nombre del paciente si viene en un objeto anidado
        paciente_info = payload.get("paciente", {})
        if isinstance(paciente_info, dict):
            nombre_paciente = paciente_info.get("nombre", "Sin nombre")
        else:
            nombre_paciente = str(paciente_info)

        # 3. Convertir a string JSON válido para PostgreSQL (JSONB)
        # Esto evita el error 'invalid input syntax for type json'
        json_string = json.dumps(payload)

        # 4. Insertar en la base de datos
        conn = psycopg2.connect(DATABASE_URL)
        cur = conn.cursor()
        query = """
            INSERT INTO webhooks_dentalink (evento_tipo, paciente_nombre, datos_json)
            VALUES (%s, %s, %s)
        """
        cur.execute(query, (evento, nombre_paciente, json_string))
        
        conn.commit()
        cur.close()
        conn.close()

        return {"status": "success", "message": "Evento registrado"}

    except Exception as e:
        # Si algo falla, devolvemos el error para debugear en el cURL
        return {"status": "error", "message": str(e)}

if __name__ == "__main__":
    import uvicorn
    # Puerto 8000 para que coincida con la configuración de Coolify
    uvicorn.run(app, host="0.0.0.0", port=8000)