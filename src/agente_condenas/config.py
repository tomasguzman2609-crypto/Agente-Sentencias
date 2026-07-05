"""
Esquema de extracción para el agente de análisis de sentencias/condenas.

Cada campo (salvo los marcados como "sintesis") exige que el modelo entregue
una cita textual EXACTA (verbatim) y la página donde aparece. Esto es lo que
permite verificar automáticamente si el dato es real o si el modelo alucinó.
"""

# Nombre de columna (tal como lo pidió el usuario) -> clave interna
CAMPOS = {
    "TRIBUNAL DE ORIGEN": "tribunal_origen",
    "ROL DE INSTANCIA": "rol_instancia",
    "ROL CORTE SUPREMA": "rol_corte_suprema",
    "RESUMEN CAUSA": "resumen_causa",                # síntesis, no 100% verificable literalmente
    "DELITO O DELITOS DISCUTIDOS": "delitos_discutidos",
    "RECURSO PRESENTADO": "recurso_presentado",
    "DECISIÓN DEL TRIBUNAL": "decision_tribunal",
    "ARTÍCULOS DESTACADOS": "articulos_destacados",
    "REFERENCIA JURISPRUDENCIAL EN SENTENCIAS": "referencia_jurisprudencial",
    "NOMBRE JUEZ DE PRIMERA INSTANCIA": "juez_primera_instancia",
    "MINISTROS DE CORTE SUPREMA QUE INTEGRARON SALA": "ministros_corte_suprema",
    "¿EXISTE VOTO DISIDENTE? QUE DICE.": "voto_disidente",
}

# Campos que son síntesis editorial (no una cita literal única) y por lo tanto
# SIEMPRE se marcan para revisión humana, sin importar el resultado de la verificación.
CAMPOS_SINTESIS = {"resumen_causa"}

# Modelo y parámetros. Temperatura 0 = determinístico, sin creatividad.
# Gemini 2.5 Pro: buen equilibrio precisión/costo para extracción legal larga.
# Alternativas más nuevas (revisa disponibilidad en tu cuenta): "gemini-3.1-pro-preview", "gemini-3.5-flash".
MODEL = "gemini-2.5-flash"
MODEL_ECONOMICO = "gemini-2.5-flash"  # alternativa más económica si el volumen es alto
TEMPERATURE = 0
MAX_OUTPUT_TOKENS = 8000

SYSTEM_PROMPT = """Eres un asistente de extracción de información jurídica. Tu único trabajo es \
leer el texto de una sentencia judicial chilena y extraer datos objetivos, EXACTAMENTE como \
aparecen en el documento. No interpretas, no opinas, no completas información faltante.

REGLAS ESTRICTAS (no negociables):
1. Para cada campo (excepto "resumen_causa"), debes incluir:
   - "valor": el dato extraído, tal como aparece en el documento.
   - "cita_textual": una cita EXACTA y literal (máx. 25 palabras) copiada del documento, \
que respalde ese valor. Debe ser un copy-paste real del texto, sin parafrasear.
   - "pagina": el número de página (entero) donde se encuentra esa cita, según los \
marcadores "[PÁGINA N]" que verás en el texto.
2. Si un dato NO aparece explícitamente en el documento, el campo completo debe ser:
   {"valor": null, "cita_textual": null, "pagina": null}
   NUNCA inventes, infieras agresivamente ni completes con conocimiento externo.
3. "resumen_causa" es la única excepción: es una síntesis breve (2-4 frases) en tus \
propias palabras de los hechos y el curso procesal. Aun así, básate solo en lo que dice \
el documento.
4. "voto_disidente" tiene esta forma:
   {"existe": true/false, "contenido": "resumen del voto o null", "cita_textual": "...", "pagina": N}
   Si no existe voto disidente, existe=false y el resto null.
5. Responde ÚNICAMENTE con un objeto JSON válido, sin texto adicional, sin markdown, \
sin ```json. Las claves deben ser exactamente las indicadas en el schema.
"""
