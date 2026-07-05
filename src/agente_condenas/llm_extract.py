import json
from google import genai
from google.genai import types
from config import SYSTEM_PROMPT, CAMPOS, MODEL, TEMPERATURE, MAX_OUTPUT_TOKENS

_client = None


def _get_client():
    global _client
    if _client is None:
        _client = genai.Client()  # toma GEMINI_API_KEY (o GOOGLE_API_KEY) del entorno
    return _client


SCHEMA_KEYS = list(CAMPOS.values())


def _campo_con_cita(descripcion_valor: str = "El dato extraído, tal como aparece en el documento."):
    """Bloque repetido: valor + cita textual + página, todo nullable."""
    return {
        "type": "OBJECT",
        "properties": {
            "valor": {"type": "STRING", "nullable": True, "description": descripcion_valor},
            "cita_textual": {
                "type": "STRING",
                "nullable": True,
                "description": "Cita EXACTA y literal (máx. 25 palabras) copiada del documento.",
            },
            "pagina": {
                "type": "INTEGER",
                "nullable": True,
                "description": "Número de página donde aparece la cita, según los marcadores [PÁGINA N].",
            },
        },
        "required": ["valor", "cita_textual", "pagina"],
    }


def _construir_schema() -> dict:
    propiedades = {}
    for clave in SCHEMA_KEYS:
        if clave == "resumen_causa":
            propiedades[clave] = {
                "type": "OBJECT",
                "properties": {
                    "valor": {
                        "type": "STRING",
                        "description": "Síntesis breve (2-4 frases) en tus propias palabras.",
                    }
                },
                "required": ["valor"],
            }
        elif clave == "voto_disidente":
            propiedades[clave] = {
                "type": "OBJECT",
                "properties": {
                    "existe": {"type": "BOOLEAN"},
                    "contenido": {"type": "STRING", "nullable": True},
                    "cita_textual": {"type": "STRING", "nullable": True},
                    "pagina": {"type": "INTEGER", "nullable": True},
                },
                "required": ["existe", "contenido", "cita_textual", "pagina"],
            }
        else:
            propiedades[clave] = _campo_con_cita()

    return {"type": "OBJECT", "properties": propiedades, "required": SCHEMA_KEYS}


RESPONSE_SCHEMA = _construir_schema()


def extraer_campos(texto_documento: str, model: str = MODEL) -> dict:
    """
    Llama a Gemini con temperature=0 y response_schema forzado. Devuelve el
    JSON ya parseado con los campos, sus citas textuales y páginas.
    """
    prompt_usuario = f"""Extrae los datos del siguiente documento judicial siguiendo el schema \
provisto.

--- DOCUMENTO (con marcadores de página) ---
{texto_documento}
"""

    config = types.GenerateContentConfig(
        temperature=TEMPERATURE,
        max_output_tokens=MAX_OUTPUT_TOKENS,
        system_instruction=SYSTEM_PROMPT,
        response_mime_type="application/json",
        response_schema=RESPONSE_SCHEMA,
    )

    respuesta = _get_client().models.generate_content(
        model=model,
        contents=prompt_usuario,
        config=config,
    )

    try:
        return json.loads(respuesta.text)
    except json.JSONDecodeError as e:
        raise ValueError(
            f"El modelo no devolvió JSON válido. Respuesta cruda:\n{respuesta.text}"
        ) from e
