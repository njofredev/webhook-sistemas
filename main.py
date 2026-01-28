from fastapi import FastAPI, Request
import psycopg2
import os

app = FastAPI()

# Configuración de conexión (usa variables de entorno en Coolify)
DATABASE_URL = os.getenv("DATABASE_URL")

def get_db_connection():
    return psycopg2.connect(DATABASE_URL)

@app.post("/webhook")
async def receive_webhook(request: Request):
    payload = await request.json()
    
    # Extraemos info básica del webhook de Dentalink
    # Nota: Ajusta las llaves según el JSON real que envía Dentalink
    tipo = payload.get("nombre_evento", "desconocido")
    nombre_paciente = payload.get("paciente", {}).get("nombre", "N/A")

    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute(
        "INSERT INTO webhooks_dentalink (evento_tipo, paciente_nombre, datos_json) VALUES (%s, %s, %s)",
        (tipo, nombre_paciente, str(payload))
    )
    conn.commit()
    cur.close()
    conn.close()
    
    return {"status": "received"}