"""
Postulaciones automatizadas — Andrés Carrizo
=============================================
Por cada entrada en jobs.json:
  1. Genera una carta personalizada con Claude
  2. Crea un borrador en Gmail con la carta y el CV adjunto

Uso:
    python main.py            # procesa todos los jobs
    python main.py --dry-run  # genera cartas pero NO toca Gmail (para revisar)
"""

import os
import json
import argparse
from datetime import datetime
from pathlib  import Path
from dotenv   import load_dotenv
import anthropic

from gmail_auth  import get_gmail_service
from carta       import generar_todo
from draft       import crear_borrador
from cv_adapter  import adaptar_cv, limpiar_temporales

load_dotenv()

JOBS_FILE      = Path(__file__).parent / "jobs.json"
BORRADORES_DIR = Path(__file__).parent / "borradores"


def log_resultado(job: dict, draft_id: str | None, carta: str) -> None:
    """Guarda un registro de cada borrador creado."""
    BORRADORES_DIR.mkdir(exist_ok=True)
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    nombre = f"{ts}_{job['empresa'].replace(' ', '_')}.txt"
    contenido = (
        f"Empresa : {job['empresa']}\n"
        f"Rol     : {job['rol']}\n"
        f"Email   : {job['email']}\n"
        f"CV      : {job['cv']}\n"
        f"Draft ID: {draft_id or 'ERROR'}\n"
        f"Fecha   : {datetime.now().isoformat()}\n"
        f"\n{'='*50}\nCARTA:\n{'='*50}\n{carta}\n"
    )
    (BORRADORES_DIR / nombre).write_text(contenido, encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--dry-run", action="store_true",
                        help="Genera cartas y las muestra, pero no crea borradores en Gmail")
    args = parser.parse_args()

    # ── Cargar jobs ──────────────────────────────────────────────────────────
    if not JOBS_FILE.exists():
        print("[ERROR] No encontré jobs.json")
        return

    jobs = json.loads(JOBS_FILE.read_text(encoding="utf-8"))

    # Saltear las que ya fueron procesadas
    pendientes = [j for j in jobs if not j.get("enviado")]
    ya_enviadas = len(jobs) - len(pendientes)

    print(f"{'='*55}")
    print(f"  Postulaciones – Andrés Carrizo")
    print(f"  {len(pendientes)} nuevas | {ya_enviadas} ya enviadas | modo: {'DRY-RUN' if args.dry_run else 'REAL (crea borradores)'}")
    print(f"{'='*55}\n")

    if not pendientes:
        print("  No hay postulaciones nuevas. Agregá empresas a jobs.json.")
        return

    jobs = pendientes

    # ── Autenticación ────────────────────────────────────────────────────────
    api_key = os.getenv("ANTHROPIC_API_KEY")
    if not api_key:
        print("[ERROR] Falta ANTHROPIC_API_KEY en .env")
        return

    claude = anthropic.Anthropic(api_key=api_key)

    if not args.dry_run:
        print("Conectando con Gmail...")
        service = get_gmail_service()
        print("  Gmail OK\n")
    else:
        service = None

    # ── Procesar cada postulación ────────────────────────────────────────────
    ok = 0
    errores = 0

    for i, job in enumerate(jobs, 1):
        print(f"[{i}/{len(jobs)}] {job['empresa']} — {job['rol']}")

        # Generar carta + keywords + resumen con Claude
        try:
            resultado  = generar_todo(job["empresa"], job["rol"], job.get("descripcion", ""), claude)
            carta      = resultado["carta"]
            resumen    = resultado["resumen"]
            keywords   = resultado["keywords"]
            print(f"  ✓ Carta generada | Keywords: {', '.join(keywords[:4])}")
        except Exception as e:
            print(f"  ✗ Error generando carta: {e}")
            errores += 1
            continue

        # Adaptar CV con resumen personalizado
        try:
            cv_adaptado = adaptar_cv(job["cv"], resumen, keywords, job["empresa"])
            job_con_cv  = {**job, "cv": cv_adaptado}
            print(f"  ✓ CV adaptado: {cv_adaptado}")
        except Exception as e:
            print(f"  [!] No se pudo adaptar CV ({e}), usando original")
            job_con_cv = job

        if args.dry_run:
            separador = "-" * 50
            print(f"\n{separador}")
            print(f"PARA  : {job['email']}")
            print(f"ASUNTO: Postulación — {job['rol']} | Andrés Carrizo")
            print(f"CV    : {job_con_cv['cv']}")
            print(f"RESUMEN CV: {resumen}")
            print(f"KEYWORDS  : {', '.join(keywords)}")
            print(f"\n{carta}\n{separador}\n")
            ok += 1
            continue

        # Crear borrador en Gmail
        draft_id = crear_borrador(service, job_con_cv, carta)
        if draft_id:
            print(f"  ✓ Borrador creado (ID: {draft_id})")
            log_resultado(job, draft_id, carta)
            job["enviado"] = True   # marcar como procesada
            ok += 1
        else:
            print(f"  ✗ Falló la creación del borrador")
            log_resultado(job, None, carta)
            errores += 1

    # Guardar jobs.json con los marcados como enviados
    todos = json.loads(JOBS_FILE.read_text(encoding="utf-8"))
    enviados_emails = {j["email"] for j in jobs if j.get("enviado")}
    for j in todos:
        if j["email"] in enviados_emails:
            j["enviado"] = True
    JOBS_FILE.write_text(json.dumps(todos, ensure_ascii=False, indent=2), encoding="utf-8")

    # ── Resumen final ────────────────────────────────────────────────────────
    print(f"\n{'='*55}")
    print(f"  Exitosos : {ok}")
    print(f"  Errores  : {errores}")
    if not args.dry_run and ok > 0:
        print(f"\n  Abrí Gmail → Borradores y revisá antes de enviar.")
        print(f"  Logs en: borradores/")
    limpiar_temporales()
    print(f"{'='*55}")


if __name__ == "__main__":
    main()
