"""
Autenticación OAuth2 con Gmail API.
La primera vez abre el navegador para que des permiso.
A partir de ahí guarda el token en token.json y se renueva solo.
"""

import os
from pathlib import Path
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

# Solo necesitamos permiso para crear borradores
SCOPES = [
    "https://www.googleapis.com/auth/gmail.modify",   # leer + crear borradores
    "https://www.googleapis.com/auth/calendar.events",
]

CREDENTIALS_FILE = Path(__file__).parent / "credentials.json"
TOKEN_FILE       = Path(__file__).parent / "token.json"


def get_gmail_service():
    """
    Retorna un cliente autenticado de Gmail API.
    - Si ya existe token.json válido → lo usa directamente.
    - Si el token expiró → lo renueva automáticamente.
    - Si no hay token → abre el navegador para autorizar (solo la primera vez).
    """
    creds = None

    if TOKEN_FILE.exists():
        creds = Credentials.from_authorized_user_file(str(TOKEN_FILE), SCOPES)

    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            if not CREDENTIALS_FILE.exists():
                raise FileNotFoundError(
                    "\n[ERROR] No encontré credentials.json.\n"
                    "Seguí los pasos de SETUP.md para descargarlo desde Google Cloud Console."
                )
            flow = InstalledAppFlow.from_client_secrets_file(str(CREDENTIALS_FILE), SCOPES)
            creds = flow.run_local_server(port=0)

        # Guardar para la próxima vez
        TOKEN_FILE.write_text(creds.to_json(), encoding="utf-8")
        print("  Token guardado en token.json")

    return build("gmail", "v1", credentials=creds)
