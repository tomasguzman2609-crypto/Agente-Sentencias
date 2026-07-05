"""
Verificación anti-alucinación.

No confiamos en que el modelo "diga la verdad" solo porque se lo pedimos.
Este módulo re-chequea, con código determinístico (no otro LLM), que cada
cita_textual que el modelo entregó exista realmente en el texto de la página
que indicó. Si no aparece, el campo se marca como NO_VERIFICADO en vez de
darlo por bueno.
"""
import re
from config import CAMPOS_SINTESIS

UMBRAL_SIMILITUD = 0.85  # tolerante a saltos de línea / espacios de OCR


def _normalizar(s: str) -> str:
    s = s.lower()
    s = re.sub(r"\s+", " ", s)
    s = re.sub(r"[^\w\s]", "", s)
    return s.strip()


def _cita_existe_en_pagina(cita: str, texto_pagina: str) -> bool:
    if not cita or not texto_pagina:
        return False
    cita_n = _normalizar(cita)
    texto_n = _normalizar(texto_pagina)
    if cita_n in texto_n:
        return True
    # tolerancia: exige que al menos el 85% de las palabras de la cita
    # aparezcan en orden dentro del texto (por si el OCR cambió un carácter)
    palabras = cita_n.split()
    if len(palabras) < 3:
        return False
    encontradas = sum(1 for p in palabras if p in texto_n)
    return (encontradas / len(palabras)) >= UMBRAL_SIMILITUD


def verificar_extraccion(extraccion: dict, texto_por_pagina: dict) -> dict:
    """
    Añade a cada campo un sub-campo "estado":
      - "VERIFICADO"    -> la cita existe literalmente en la página indicada
      - "NO_VERIFICADO" -> el modelo dio una cita pero no se encontró
      - "NO_ENCONTRADO" -> el modelo indicó que el dato no está en el documento
      - "SINTESIS"      -> campo editorial (resumen_causa), siempre a revisar
    """
    resultado = {}
    for clave, valor in extraccion.items():
        if clave in CAMPOS_SINTESIS:
            resultado[clave] = {**valor, "estado": "SINTESIS"}
            continue

        if clave == "voto_disidente":
            if not valor.get("existe"):
                resultado[clave] = {**valor, "estado": "NO_ENCONTRADO"}
                continue
            cita = valor.get("cita_textual")
            pagina = valor.get("pagina")
            texto_pag = texto_por_pagina.get(pagina, "")
            estado = "VERIFICADO" if _cita_existe_en_pagina(cita, texto_pag) else "NO_VERIFICADO"
            resultado[clave] = {**valor, "estado": estado}
            continue

        cita = valor.get("cita_textual")
        pagina = valor.get("pagina")

        if valor.get("valor") is None:
            resultado[clave] = {**valor, "estado": "NO_ENCONTRADO"}
            continue

        texto_pag = texto_por_pagina.get(pagina, "")
        estado = "VERIFICADO" if _cita_existe_en_pagina(cita, texto_pag) else "NO_VERIFICADO"
        resultado[clave] = {**valor, "estado": estado}

    return resultado
