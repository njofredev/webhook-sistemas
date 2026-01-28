import os
from fastapi import FastAPI, Request
import psycopg2
from psycopg2.extras import RealDictCursor

app = FastAPI()

# Obtiene la URL desde las variables de entorno de Coolify
DATABASE_URL = os.getenv("DATABASE_URL")

@app.post("/webhook")
async def handle_webhook(request: Request):
    data = await request.json()
    
    # Ejemplo de cómo filtrar y categorizar básico:
    # Ajustar según lo que envíe Dentalink (ej: id_estado o nombre_evento)
    evento = data.get("evento", "desconocido") 
    paciente = data.get("paciente", {}).get("nombre", "Sin Nombre")

    try:
        conn = psycopg2.connect(DATABASE_URL)
        cur = conn.cursor()
        query = """
            INSERT INTO webhooks_dentalink (evento_tipo, paciente_nombre, datos_json)
            VALUES (%s, %s, %s)
        """
        cur.execute(query, (evento, paciente, str(data)))
        conn.commit()
        cur.close()
        conn.close()
        return {"status": "ok"}
    except Exception as e:
        return {"status": "error", "message": str(e)}