import os

import psycopg2
from dotenv import load_dotenv

load_dotenv()

# URL de conexion (cambiala por la tuya si es necesario)
DATABASE_URL = os.getenv("DATABASE_URL")


def reset_database() -> None:
    """Reinicia el esquema public usando la conexion configurada."""
    try:
        if not DATABASE_URL:
            raise ValueError("DATABASE_URL no esta configurada")

        conn = psycopg2.connect(DATABASE_URL)
        conn.autocommit = True
        cur = conn.cursor()

        print("Eliminando esquema public...")
        cur.execute("DROP SCHEMA public CASCADE;")

        print("Creando esquema public...")
        cur.execute("CREATE SCHEMA public;")

        print("Restaurando permisos...")
        cur.execute("GRANT ALL ON SCHEMA public TO public;")

        print("Base de datos reseteada correctamente.")

        cur.close()
        conn.close()
    except Exception as e:
        print("Error reseteando la base de datos:", e)


if __name__ == "__main__":
    reset_database()
