"""
Error Trigger: aviso al administrador por email cuando el flujo principal
tiene fallas, para que alguien humano se entere sin tener que revisar la
consola o esperar a que el usuario final se queje.

Requiere estas variables de entorno (ver .env.example):
  SMTP_HOST, SMTP_PORT, SMTP_USER, SMTP_PASSWORD, ADMIN_EMAIL

Si no están configuradas, no rompe el flujo: solo imprime el aviso en
consola (fail-safe) para que procesar los PDFs no dependa del envío de
correo.
"""
import os
import smtplib
from email.mime.text import MIMEText


def avisar_error_admin(asunto: str, cuerpo: str):
    host = os.environ.get("SMTP_HOST")
    puerto = os.environ.get("SMTP_PORT")
    usuario = os.environ.get("SMTP_USER")
    password = os.environ.get("SMTP_PASSWORD")
    destinatario = os.environ.get("ADMIN_EMAIL")

    if not all([host, puerto, usuario, password, destinatario]):
        print(f"  ⚠️  [Error Trigger sin configurar] {asunto}\n{cuerpo}")
        return

    msg = MIMEText(cuerpo)
    msg["Subject"] = asunto
    msg["From"] = usuario
    msg["To"] = destinatario

    try:
        with smtplib.SMTP(host, int(puerto)) as server:
            server.starttls()
            server.login(usuario, password)
            server.sendmail(usuario, [destinatario], msg.as_string())
        print(f"  ✉️  Aviso de error enviado a {destinatario}")
    except Exception as e:
        print(f"  ⚠️  No se pudo enviar el aviso por email ({e}). Detalle:\n{cuerpo}")
