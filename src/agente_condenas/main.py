"""
Pipeline completo:
  1. Lista PDFs de la carpeta de Drive.
  2. Salta los que ya se procesaron OK en una corrida anterior (no vuelve
     a gastar tokens de Gemini con el mismo documento).
  3. Descarga cada PDF nuevo (con reintentos si la API de Drive falla).
  4. Extrae texto (con OCR de respaldo si es necesario).
  5. Llama al modelo (temperature=0, con reintentos) para extraer campos + citas.
  6. Verifica cada cita contra el texto real del documento.
  7. Registra el resultado (OK/ERROR) + la extracción completa en la BBDD.
  8. Si un PDF falla, el flujo sigue con los demás (continue on fail).
  9. Reconstruye la tabla Excel con TODOS los PDFs ya procesados (viejos +
     nuevos), leyendo la BBDD — así el Excel siempre queda consolidado sin
     tener que reprocesar nada.
  10. Si hubo errores, avisa al admin por email (error trigger).

Uso:
  export GEMINI_API_KEY=...
  export GOOGLE_SERVICE_ACCOUNT_JSON=/ruta/credenciales.json
  python main.py --carpeta-id <ID_CARPETA_DRIVE> --salida sentencias.xlsx
"""
import argparse
import os
import tempfile

from extract_text import extraer_texto_con_paginas
from llm_extract import extraer_campos
from verificar import verificar_extraccion
from output_table import construir_tabla
from reintentos import con_reintentos
from logging_db import registrar_ejecucion, archivos_ya_procesados_ok, obtener_extracciones_ok
from notificaciones import avisar_error_admin
import drive_sync


def procesar_un_pdf(pdf_id: str, nombre: str, carpeta_temp: str) -> dict:
    pdf_local = os.path.join(carpeta_temp, nombre)
    con_reintentos(drive_sync.descargar_pdf, pdf_id, pdf_local)

    texto_completo, texto_por_pagina, paginas_ocr = extraer_texto_con_paginas(pdf_local)
    if paginas_ocr:
        print(f"  [{nombre}] OCR aplicado en páginas: {paginas_ocr}")

    extraccion_cruda = con_reintentos(extraer_campos, texto_completo)
    extraccion_verificada = verificar_extraccion(extraccion_cruda, texto_por_pagina)

    return extraccion_verificada


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--carpeta-id", required=True, help="ID de la carpeta de Google Drive con los PDF")
    parser.add_argument("--salida", default="sentencias.xlsx")
    args = parser.parse_args()

    todos_los_pdfs = drive_sync.listar_pdfs(args.carpeta_id)
    ya_procesados = archivos_ya_procesados_ok()
    pendientes = [pdf for pdf in todos_los_pdfs if pdf["name"] not in ya_procesados]
    saltados = len(todos_los_pdfs) - len(pendientes)

    print(f"{len(todos_los_pdfs)} PDF(s) en la carpeta · {saltados} ya procesado(s) antes (se saltan) · {len(pendientes)} nuevo(s) por procesar.")

    errores = []
    with tempfile.TemporaryDirectory() as tmp:
        for archivo in pendientes:
            print(f"Procesando: {archivo['name']}")
            try:
                extraccion = procesar_un_pdf(archivo["id"], archivo["name"], tmp)
                registrar_ejecucion(archivo["name"], "OK", extraccion=extraccion)
            except Exception as e:
                print(f"  ⚠️  Error con {archivo['name']}: {e}")
                registrar_ejecucion(archivo["name"], "ERROR", str(e))
                errores.append((archivo["name"], str(e)))
                continue  # continue on fail: seguimos con el resto

    # La tabla final se arma con TODO lo que está OK en la BBDD (corridas
    # anteriores incluidas), no solo con lo procesado en esta corrida.
    filas = obtener_extracciones_ok()
    construir_tabla(filas, args.salida)
    print(f"\nListo. Tabla consolidada guardada en: {args.salida}")
    print(f"Total en la tabla: {len(filas)} · Nuevos esta corrida: {len(pendientes) - len(errores)} · Con error: {len(errores)}")

    if errores:
        detalle = "\n".join(f"- {nombre}: {err}" for nombre, err in errores)
        avisar_error_admin(
            asunto=f"[agente_condenas] {len(errores)} PDF(s) fallaron",
            cuerpo=f"La corrida de hoy tuvo errores en {len(errores)} archivo(s):\n\n{detalle}",
        )


if __name__ == "__main__":
    main()