import sqlite3
from datetime import datetime

DB_NAME = "registros.db"

def crear_tabla():
    conn = sqlite3.connect(DB_NAME)
    cur = conn.cursor()
    cur.execute("""
        CREATE TABLE IF NOT EXISTS registros (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            fecha TEXT NOT NULL,
            lechugas INTEGER,
            temperatura REAL,
            humedad REAL
        )
    """)
    conn.commit()
    conn.close()

def guardar_registro(lechugas, temperatura, humedad):
    conn = sqlite3.connect(DB_NAME)
    cur = conn.cursor()
    fecha = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    cur.execute("""
        INSERT INTO registros (fecha, lechugas, temperatura, humedad)
        VALUES (?, ?, ?, ?)
    """, (fecha, lechugas, temperatura, humedad))

    conn.commit()
    conn.close()

# Crear tabla automáticamente al importar
crear_tabla()
