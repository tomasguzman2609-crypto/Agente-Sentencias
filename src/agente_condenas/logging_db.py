"""
Registro de ejecuciones en una base de datos (SQLite local por defecto).

El proyecto no requiere una BBDD para el negocio (los datos extraídos van a
un Excel consolidado, que es el entregable que usa el usuario final), pero
la pauta exige como mínimo guardar logs de ejecución en una BBDD real. Esta
tabla registra, por cada PDF procesado: nombre, resultado, error (si lo
hubo), la extracción completa (como JSON, si fue OK) y timestamp.

Guardar la extracción completa permite además NO reprocesar un PDF que ya
se leyó bien en una corrida anterior — si se agregan PDFs nuevos a la
carpeta de a poco, el agente solo llama a Gemini con los nuevos y
reconstruye la tabla consolidada completa (viejos + nuevos) leyendo esta
BBDD, sin gastar tokens de más.

Si el equipo prefiere Supabase/Postgres en vez de SQLite, basta con
reemplazar la conexión de este módulo (misma interfaz) y mantener el resto
del pipeline intacto.
"""
import sqlite3
import json
from datetime import datetime, timezone

DB_PATH = "ejecuciones.db"


def _conectar():
    conn = sqlite3.connect(DB_PATH)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS ejecuciones (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            archivo TEXT NOT NULL,
            estado TEXT NOT NULL,      -- 'OK' o 'ERROR'
            detalle TEXT,              -- mensaje de error, si aplica
            extraccion_json TEXT,      -- extracción completa, si estado='OK'
            timestamp TEXT NOT NULL
        )
    """)
    return conn


def registrar_ejecucion(archivo: str, estado: str, detalle: str = None, extraccion: dict = None):
    conn = _conectar()
    with conn:
        conn.execute(
            "INSERT INTO ejecuciones (archivo, estado, detalle, extraccion_json, timestamp) VALUES (?, ?, ?, ?, ?)",
            (
                archivo,
                estado,
                detalle,
                json.dumps(extraccion, ensure_ascii=False) if extraccion else None,
                datetime.now(timezone.utc).isoformat(),
            ),
        )
    conn.close()


def obtener_historial(limite: int = 50):
    conn = _conectar()
    filas = conn.execute(
        "SELECT archivo, estado, detalle, timestamp FROM ejecuciones ORDER BY id DESC LIMIT ?",
        (limite,),
    ).fetchall()
    conn.close()
    return filas


def archivos_ya_procesados_ok() -> set[str]:
    """Nombres de archivo que ya tienen al menos una ejecución con estado 'OK'."""
    conn = _conectar()
    filas = conn.execute(
        "SELECT DISTINCT archivo FROM ejecuciones WHERE estado = 'OK'"
    ).fetchall()
    conn.close()
    return {fila[0] for fila in filas}


def obtener_extracciones_ok() -> list[dict]:
    """Última extracción OK de cada archivo, lista para construir la tabla
    consolidada completa (incluye PDFs de corridas anteriores)."""
    conn = _conectar()
    filas = conn.execute("""
        SELECT archivo, extraccion_json FROM ejecuciones e
        WHERE estado = 'OK'
        AND id = (
            SELECT MAX(id) FROM ejecuciones e2
            WHERE e2.archivo = e.archivo AND e2.estado = 'OK'
        )
        ORDER BY archivo
    """).fetchall()
    conn.close()
    return [
        {"nombre_archivo": archivo, "extraccion": json.loads(extraccion_json)}
        for archivo, extraccion_json in filas
    ]


def archivos_ya_procesados_ok() -> set[str]:
    """Nombres de archivo que ya tienen al menos una ejecución con estado 'OK'.

    Se usa para no volver a llamar a Gemini con un PDF que ya se procesó
    bien en una corrida anterior — evita gastar tokens dos veces con el
    mismo documento si se agregan PDFs nuevos a la carpeta de a poco.
    """
    conn = _conectar()
    filas = conn.execute(
        "SELECT DISTINCT archivo FROM ejecuciones WHERE estado = 'OK'"
    ).fetchall()
    conn.close()
    return {fila[0] for fila in filas}