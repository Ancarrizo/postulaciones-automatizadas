"""
Lee la casilla de Gmail buscando vacantes de Computrabajo, LinkedIn, etc.
Por cada vacante nueva genera una carta y crea un borrador listo para enviar.
"""

import base64
import json
import re
import os
from pathlib  import Path
from dotenv   import load_dotenv
import anthropic

from gmail_auth import get_gmail_service
from carta      import generar_carta
from draft      import crear_borrador

load_dotenv()

JOBS_FILE     = Path(__file__).parent / "jobs.json"
LEIDOS_FILE   = Path(__file__).parent / "vacantes_leidas.json"

# Remitentes conocidos de portales de empleo
PORTALES = [
    "computrabajo.com.ar",
    "linkedin.com",
    "zonajobs.com.ar",
    "bumeran.com.ar",
    "indeed.com",
]

# Query para buscar en Gmail
GMAIL_QUERY = " OR ".join(f"from:{p}" for p in PORTALES)


def cargar_leidos() -> set:
    if LEIDOS_FILE.exists():
        return set(json.loads(LEIDOS_FILE.read_text(encoding="utf-8")))
    return set()


def guardar_leidos(leidos: set) -> None:
    LEIDOS_FILE.write_text(json.dumps(list(leidos), ensure_ascii=False, indent=2), encoding="utf-8")


def get_email_body(service, msg_id: str) -> str:
    """Extrae el texto del email."""
    msg = service.users().messages().get(userId="me", id=msg_id, format="full").execute()
    payload = msg.get("payload", {})

    def extract_text(part):
        if part.get("mimeType") == "text/plain":
            data = part.get("body", {}).get("data", "")
            return base64.urlsafe_b64decode(data).decode("utf-8", errors="ignore")
        for sub in part.get("parts", []):
            result = extract_text(sub)
            if result:
                return result
        return ""

    return extract_text(payload)


def extraer_vacante_con_claude(asunto: str, cuerpo: str, client: anthropic.Anthropic) -> dict | None:
    """
    Usa Claude para extraer empresa, rol y email de contacto del email de vacante.
    Retorna None si no parece una vacante relevante.
    """
    prompt = f"""Analizá este email de un portal de empleo y extraé la información de la vacante.

ASUNTO: {asunto}

CUERPO:
{cuerpo[:3000]}

Respondé SOLO con un JSON con este formato exacto (sin markdown):
{{
  "es_vacante": true/false,
  "empresa": "nombre de la empresa o null",
  "rol": "nombre del puesto o null",
  "email_contacto": "email de contacto o null",
  "url": "link a la oferta o null"
}}

IMPORTANTE: Si el email menciona UNA O MÁS ofertas de trabajo concretas, poné es_vacante: true y extraé la primera oferta.
Solo poné es_vacante: false si es un email completamente genérico sin ningún puesto mencionado."""

    resp = client.messages.create(
        model="claude-sonnet-4-5",
        max_tokens=300,
        messages=[{"role": "user", "content": prompt}],
    )

    try:
        data = json.loads(resp.content[0].text.strip())
        if not data.get("es_vacante"):
            return None
        if not data.get("empresa") or not data.get("rol"):
            return None
        return data
    except Exception:
        return None


def ya_en_jobs(empresa: str, email: str) -> bool:
    """Verifica si esta empresa ya está en jobs.json."""
    if not JOBS_FILE.exists():
        return False
    jobs = json.loads(JOBS_FILE.read_text(encoding="utf-8"))
    return any(
        j.get("empresa", "").lower() == empresa.lower() or
        j.get("email", "").lower() == email.lower()
        for j in jobs
    )


def agregar_a_jobs(vacante: dict, cv_default: str = "CV_Andres_Carrizo_2026.docx") -> None:
    """Agrega la vacante a jobs.json para el registro."""
    jobs = json.loads(JOBS_FILE.read_text(encoding="utf-8")) if JOBS_FILE.exists() else []
    jobs.append({
        "empresa": vacante["empresa"],
        "rol": vacante["rol"],
        "email": vacante.get("email_contacto") or "",
        "cv": cv_default,
        "url": vacante.get("url"),
        "enviado": False,
        "origen": "gmail_auto",
    })
    JOBS_FILE.write_text(json.dumps(jobs, ensure_ascii=False, indent=2), encoding="utf-8")


def procesar_vacantes_inbox() -> None:
    api_key = os.getenv("ANTHROPIC_API_KEY")
    if not api_key:
        print("[ERROR] Falta ANTHROPIC_API_KEY en .env")
        return

    claude  = anthropic.Anthropic(api_key=api_key)
    service = get_gmail_service()
    leidos  = cargar_leidos()

    print(f"Buscando vacantes en Gmail...")
    print(f"  Filtro: {GMAIL_QUERY}\n")

    # Buscar emails de los últimos 7 días
    resultados = (
        service.users()
        .messages()
        .list(userId="me", q=f"({GMAIL_QUERY}) newer_than:7d", maxResults=50)
        .execute()
    )

    mensajes = resultados.get("messages", [])
    print(f"  {len(mensajes)} emails encontrados\n")

    nuevas = 0
    for msg in mensajes:
        msg_id = msg["id"]
        if msg_id in leidos:
            continue

        # Obtener asunto
        meta = service.users().messages().get(userId="me", id=msg_id, format="metadata",
                                               metadataHeaders=["Subject"]).execute()
        headers = {h["name"]: h["value"] for h in meta.get("payload", {}).get("headers", [])}
        asunto  = headers.get("Subject", "")

        # Obtener cuerpo
        cuerpo = get_email_body(service, msg_id)

        print(f"  Analizando: {asunto[:60]}...")

        # Extraer vacante con Claude
        vacante = extraer_vacante_con_claude(asunto, cuerpo, claude)
        leidos.add(msg_id)

        if not vacante:
            print(f"    → No es vacante relevante, salteo")
            continue

        empresa = vacante["empresa"]
        rol     = vacante["rol"]
        email_c = vacante.get("email_contacto") or ""

        print(f"    → Vacante: {rol} en {empresa}")

        # Verificar si ya la tenemos
        if ya_en_jobs(empresa, email_c):
            print(f"    → Ya estaba en jobs.json, salteo")
            continue

        # Generar carta
        carta = generar_carta(empresa, rol, claude)
        print(f"    → Carta generada")

        # Crear borrador si hay email de contacto
        if email_c:
            job_temp = {
                "empresa": empresa,
                "rol": rol,
                "email": email_c,
                "cv": "CV_Andres_Carrizo_2026.docx",
                "url": vacante.get("url"),
            }
            draft_id = crear_borrador(service, job_temp, carta)
            if draft_id:
                print(f"    → Borrador creado en Gmail ✓")
            else:
                print(f"    → No se pudo crear el borrador")
        else:
            print(f"    → Sin email de contacto — guardado en jobs.json para seguimiento")

        agregar_a_jobs(vacante)
        nuevas += 1

    guardar_leidos(leidos)

    print(f"\n{'='*50}")
    print(f"  Vacantes nuevas procesadas: {nuevas}")
    if nuevas > 0:
        print(f"  Revisá Gmail → Borradores")
    print(f"{'='*50}")


if __name__ == "__main__":
    procesar_vacantes_inbox()
