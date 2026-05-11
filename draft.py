"""
Crea borradores en Gmail con la carta generada y el CV adjunto.
"""

import base64
import mimetypes
from email.mime.multipart import MIMEMultipart
from email.mime.text    import MIMEText
from email.mime.base    import MIMEBase
from email              import encoders
from pathlib            import Path


REMITENTE = "Andrés Carrizo <Andicarrizo5@gmail.com>"
CVS_DIR   = Path(__file__).parent / "cvs"


def _construir_mime(para: str, asunto: str, cuerpo: str, cv_filename: str) -> MIMEMultipart:
    msg = MIMEMultipart()
    msg["From"]    = REMITENTE
    msg["To"]      = para
    msg["Subject"] = asunto

    # Cuerpo en texto plano y HTML
    msg.attach(MIMEText(cuerpo, "plain", "utf-8"))
    html = f"<html><body style='font-family:Arial,sans-serif;font-size:14px;line-height:1.6'>{cuerpo.replace(chr(10),'<br>')}</body></html>"
    msg.attach(MIMEText(html, "html", "utf-8"))

    # Adjunto CV
    cv_path = CVS_DIR / cv_filename
    if cv_path.exists():
        mime_type, _ = mimetypes.guess_type(str(cv_path))
        main_type, sub_type = (mime_type or "application/octet-stream").split("/", 1)
        with open(cv_path, "rb") as f:
            part = MIMEBase(main_type, sub_type)
            part.set_payload(f.read())
        encoders.encode_base64(part)
        part.add_header("Content-Disposition", "attachment", filename=cv_filename)
        msg.attach(part)
    else:
        print(f"  [AVISO] CV no encontrado: {cv_path} — se crea el borrador sin adjunto")

    return msg


def crear_borrador(service, job: dict, carta: str) -> str | None:
    """
    Crea un borrador en Gmail.
    Retorna el ID del borrador si fue exitoso, None si falló.
    """
    asunto = f"Postulación — {job['rol']} | Andrés Carrizo"

    msg = _construir_mime(
        para        = job["email"],
        asunto      = asunto,
        cuerpo      = carta,
        cv_filename = job["cv"],
    )

    raw = base64.urlsafe_b64encode(msg.as_bytes()).decode("utf-8")

    try:
        draft = (
            service.users()
            .drafts()
            .create(userId="me", body={"message": {"raw": raw}})
            .execute()
        )
        return draft["id"]
    except Exception as e:
        print(f"  [ERROR Gmail] {e}")
        return None
