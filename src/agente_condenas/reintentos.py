"""
Mecanismo de reintentos (retries) para llamadas que pueden fallar de forma
transitoria: API de Gemini, API de Google Drive.

No es un decorador mágico: es una función simple, fácil de explicar en un
Q&A. Reintenta con backoff exponencial (1s, 2s, 4s...) y deja pasar la
excepción original si se agotan los intentos, para que quien llama decida
qué hacer (por ejemplo, continuar con el siguiente archivo).
"""
import time


def con_reintentos(func, *args, intentos: int = 3, espera_base: float = 1.0, **kwargs):
    ultimo_error = None
    for intento in range(1, intentos + 1):
        try:
            return func(*args, **kwargs)
        except Exception as e:
            ultimo_error = e
            if intento == intentos:
                break
            espera = espera_base * (2 ** (intento - 1))
            print(f"    ↻ Intento {intento}/{intentos} falló ({e}); reintentando en {espera:.0f}s...")
            time.sleep(espera)
    raise ultimo_error
