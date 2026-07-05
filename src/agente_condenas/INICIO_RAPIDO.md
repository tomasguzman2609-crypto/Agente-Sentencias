# Inicio rápido

## 1. Instalar dependencias
```bash
cd agente_condenas
pip install -r requirements.txt
# Si vas a procesar PDFs escaneados:
sudo apt install tesseract-ocr tesseract-ocr-spa poppler-utils
```

## 2. Configurar la API key de Gemini
1. Ve a https://aistudio.google.com/apikey y genera (o regenera) tu key.
   Importante: si ya compartiste una key en un chat o mensaje, regenérala —
   una key expuesta debe tratarse como comprometida.
2. Copia `.env.example` a `.env`:
   ```bash
   cp .env.example .env
   ```
3. Abre `.env` y pega tu key en `GEMINI_API_KEY=`.

## 3. Configurar la cuenta de servicio de Google Drive
El link de la carpeta de Drive por sí solo NO es suficiente. El agente necesita
una cuenta de servicio con permiso de Editor en esa carpeta:

1. Ve a https://console.cloud.google.com/ → crea o selecciona un proyecto.
2. Habilita la "Google Drive API" (menú "APIs y servicios" → "Habilitar APIs").
3. Ve a "APIs y servicios" → "Credenciales" → "Crear credenciales" →
   "Cuenta de servicio". Dale un nombre cualquiera (ej. "agente-condenas").
4. Una vez creada, entra a la cuenta de servicio → pestaña "Claves" →
   "Agregar clave" → "Crear clave nueva" → tipo JSON. Se descarga un archivo.
5. Copia ese archivo a `credenciales/service_account.json` (dentro de esta carpeta).
6. Abre el JSON descargado y copia el valor de "client_email"
   (algo como `agente-condenas@tu-proyecto.iam.gserviceaccount.com`).
7. Ve a tu carpeta de Drive:
   https://drive.google.com/drive/folders/1azgunUsP-VlA1O-Z_m7RG5JgGv2Qflzu
   → botón "Compartir" → pega ese email → dale permiso "Editor".

## 4. Cargar las variables de entorno y ejecutar
```bash
export $(grep -v '^#' .env | xargs)
python main.py --carpeta-id "$CARPETA_DRIVE_ID" --salida sentencias.xlsx
```

El resultado queda en `sentencias.xlsx` (tabla consolidada) y los PDF
resaltados se suben de vuelta a la misma carpeta de Drive.

## Nota de seguridad
- `.env` y `credenciales/service_account.json` NUNCA deben subirse a un
  repositorio ni compartirse por chat. Ya agregamos ambos a `.gitignore`.
