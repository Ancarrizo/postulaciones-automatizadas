"""
Crea un evento recurrente diario en Google Calendar:
"Revisar y enviar postulaciones" todos los días a las 10:30am.
Correr una sola vez: python crear_evento.py
"""

from googleapiclient.discovery import build
from gmail_auth import get_gmail_service, SCOPES
from google.oauth2.credentials import Credentials
from pathlib import Path

TOKEN_FILE = Path(__file__).parent / "token.json"


def get_calendar_service():
    creds = Credentials.from_authorized_user_file(str(TOKEN_FILE), SCOPES)
    return build("calendar", "v3", credentials=creds)


def crear_evento_diario():
    # Primero autenticar Gmail (genera el token con ambos permisos)
    print("Autenticando con Google (Gmail + Calendar)...")
    get_gmail_service()

    print("Creando evento en Google Calendar...")
    calendar = get_calendar_service()

    evento = {
        "summary": "📨 Revisar y enviar postulaciones",
        "description": (
            "1. Abrí Gmail → Borradores y revisá las cartas generadas\n"
            "2. Enviá las que estén listas\n"
            "3. Si encontraste empresas nuevas, agregarlas a jobs.json"
        ),
        "start": {
            "dateTime": "2026-05-07T10:30:00",
            "timeZone": "America/Argentina/Buenos_Aires",
        },
        "end": {
            "dateTime": "2026-05-07T11:00:00",
            "timeZone": "America/Argentina/Buenos_Aires",
        },
        "recurrence": ["RRULE:FREQ=DAILY"],
        "reminders": {
            "useDefault": False,
            "overrides": [
                {"method": "popup", "minutes": 10},
            ],
        },
    }

    resultado = calendar.events().insert(calendarId="primary", body=evento).execute()
    print(f"\n✓ Evento creado: {resultado.get('htmlLink')}")
    print("  Todos los días a las 10:30am vas a recibir la notificación.")


if __name__ == "__main__":
    crear_evento_diario()
