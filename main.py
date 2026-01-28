import os
import json
import psycopg2
from fastapi import FastAPI, Request
from psycopg2.extras import RealDictCursor

app = FastAPI(title="Receptor Dinámico Policlínico Tabancura")

# URL de conexión a tu base de datos db_webhook
DATABASE_URL = os.getenv("DATABASE_URL")

def init_db():
    """Asegura la estructura de la tabla y sus columnas dinámicas."""
    try:
        conn = psycopg2.connect(DATABASE_URL)
        cur = conn.cursor()
        # Crear tabla base
        cur.execute("""
            CREATE TABLE IF NOT EXISTS webhooks_dentalink (
                id SERIAL PRIMARY KEY,
                fecha_recepcion TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                evento_tipo TEXT,
                paciente_nombre TEXT,
                datos_json JSONB,
                id_cita INTEGER,
                fecha_cita DATE,
                hora_inicio TIME,
                id_estado INTEGER,
                estado_cita TEXT,
                comentarios TEXT,
                id_sillon INTEGER
            );
        """)
        conn.commit()
        cur.close()
        conn.close()
        print("Base de datos lista y estructurada.")
    except Exception as e:
        print(f"Error en init_db: {e}")

# Inicializar estructura al arrancar
init_db()

@app.get("/")
async def health():
    return {"status": "running", "service": "webhook-receiver"}

@app.post("/webhook")
async def receive_webhook(request: Request):
    try:
        payload = await request.json()
        
        # 1. Identificar el contenedor de datos (Dentalink/Medilink suelen usar 'data')
        # Si no existe 'data', usamos el payload raíz.
        d = payload.get("data", payload) if isinstance(payload.get("data"), dict) else payload
        
        # 2. Extracción segura con operadores de cascada (OR)
        # Esto maneja que diferentes webhooks usen diferentes nombres de llaves.
        id_cita = d.get("id") or d.get("id_cita") or d.get("cita_id")
        fecha = d.get("fecha") or d.get("fecha_cita") or d.get("fecha_programada")
        hora = d.get("hora_inicio") or d.get("hora")
        id_estado = d.get("id_estado")
        estado_txt = d.get("estado_cita") or d.get("nombre_estado") or d.get("evento")
        comentarios = d.get("comentarios") or d.get("observaciones") or d.get("notas")
        id_sillon = d.get("id_sillon") or d.get("sillon_id")

        # 3. Lógica inteligente para el Nombre del Paciente
        nombre_final = "No especificado"
        p_raw = d.get("paciente") or d.get("paciente_nombre")
        
        if isinstance(p_raw, dict):
            # Caso: {"paciente": {"nombre": "Juan", "apellido": "Perez"}}
            n = p_raw.get("nombre") or p_raw.get("firstname") or ""
            a = p_raw.get("apellido") or p_raw.get("lastname") or ""
            nombre_final = f"{n} {a}".strip() or "Paciente (Objeto incompleto)"
        elif isinstance(p_raw, str):
            # Caso: {"paciente": "Juan Perez"}
            nombre_final = p_raw
        
        # 4. Definir tipo de evento para la columna principal
        evento_tipo = estado_txt if estado_txt else f"Estado {id_estado}" if id_estado else "Evento General"

        # 5. Inserción en PostgreSQL
        conn = psycopg2.connect(DATABASE_URL)
        cur = conn.cursor()
        
        query = """
            INSERT INTO webhooks_dentalink 
            (evento_tipo, paciente_nombre, datos_json, id_cita, fecha_cita, hora_inicio, id_estado, estado_cita, comentarios, id_sillon)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        """
        
        valores = (
            evento_tipo,
            nombre_final,
            json.dumps(payload), # Respaldo del JSON original completo
            id_cita,
            fecha if fecha else None,
            hora if hora else None,
            id_estado,
            estado_txt,
            comentarios,
            id_sillon
        )
        
        cur.execute(query, valores)
        conn.commit()
        cur.close()
        conn.close()
        
        return {"status": "success", "message": "Datos procesados dinámicamente"}

    except Exception as e:
        # Importante para debug en los logs de Coolify
        print(f"ERROR: {str(e)}")
        return {"status": "error", "message": str(e)}