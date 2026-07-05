"""
Extrae texto de un PDF, página por página, insertando marcadores [PÁGINA N]
que luego se usan para poder citar la página exacta de cada dato.

Si una página no tiene texto seleccionable (PDF escaneado/imagen), se hace
OCR automáticamente sobre esa página específica.
"""
import fitz  # PyMuPDF


def extraer_texto_con_paginas(pdf_path: str, min_chars_para_ocr: int = 20) -> tuple[str, dict, list]:
    """
    Devuelve:
      - texto_completo: string con marcadores [PÁGINA N] intercalados.
      - texto_por_pagina: dict {numero_pagina: texto_de_esa_pagina} (para verificación).
    """
    doc = fitz.open(pdf_path)
    partes = []
    texto_por_pagina = {}
    paginas_con_ocr = []

    for i, page in enumerate(doc):
        num_pagina = i + 1
        texto = page.get_text().strip()

        if len(texto) < min_chars_para_ocr:
            # Página probablemente escaneada -> OCR de esa página puntual
            texto = _ocr_pagina(page)
            paginas_con_ocr.append(num_pagina)

        texto_por_pagina[num_pagina] = texto
        partes.append(f"[PÁGINA {num_pagina}]\n{texto}")

    doc.close()
    texto_completo = "\n\n".join(partes)
    return texto_completo, texto_por_pagina, paginas_con_ocr


def _ocr_pagina(page, zoom: float = 2.0) -> str:
    import pytesseract
    from PIL import Image
    import io

    mat = fitz.Matrix(zoom, zoom)
    pix = page.get_pixmap(matrix=mat)
    img = Image.open(io.BytesIO(pix.tobytes("png")))
    return pytesseract.image_to_string(img, lang="spa")
