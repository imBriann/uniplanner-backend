import psycopg2
import os
from dotenv import load_dotenv
load_dotenv()
# URL de conexión de Render (cámbiala por la tuya)
DATABASE_URL = os.getenv("DATABASE_URL")

def reset_database():
    try:
        conn = psycopg2.connect(DATABASE_URL)
        conn.autocommit = True
        cur = conn.cursor()

        print("🔄 Eliminando esquema public...")
        cur.execute("DROP SCHEMA public CASCADE;")

        print("🆕 Creando esquema public...")
        cur.execute("CREATE SCHEMA public;")

        print("🔓 Restaurando permisos...")
        cur.execute("GRANT ALL ON SCHEMA public TO public;")

        print("✅ Base de datos reseteada correctamente.")

        cur.close()
        conn.close()
    except Exception as e:
        print("❌ Error reseteando la base de datos:", e)


if __name__ == "__main__":
    reset_database()
