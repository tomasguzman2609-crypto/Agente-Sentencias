"""
Integración con Google Drive usando una cuenta de servicio.

Requiere:
  pip install google-api-python-client google-auth
  Compartir la carpeta de Drive con el email de la cuenta de servicio
  (permiso "Lector" alcanza: el agente solo lee/descarga PDFs, ya no sube
  nada de vuelta a Drive).

Configura la variable de entorno GOOGLE_SERVICE_ACCOUNT_JSON con la ruta
al archivo de credenciales JSON de la cuenta de servicio.
"""
import os
import io
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseDownload
from google.oauth2 import service_account

SCOPES = ["https://www.googleapis.com/auth/drive.readonly"]


def _cliente_drive():
    creds_path = os.environ["GOOGLE_SERVICE_ACCOUNT_JSON"]
    creds = service_account.Credentials.from_service_account_file(creds_path, scopes=SCOPES)
    return build("drive", "v3", credentials=creds)


def listar_pdfs(carpeta_id: str) -> list[dict]:
    """Lista todos los PDF de la carpeta."""
    drive = _cliente_drive()
    query = f"'{carpeta_id}' in parents and mimeType='application/pdf' and trashed=false"
    resultados = drive.files().list(q=query, fields="files(id, name)").execute()
    return resultados.get("files", [])


def descargar_pdf(file_id: str, destino: str):
    drive = _cliente_drive()
    request = drive.files().get_media(fileId=file_id)
    with io.FileIO(destino, "wb") as fh:
        downloader = MediaIoBaseDownload(fh, request)
        done = False
        while not done:
            _, done = downloader.next_chunk()
