"""
Web app para el sistema de postulaciones de Andrés Carrizo.
Correr: python web/app.py
Abrir:  http://localhost:5000
"""

import os
import json
import subprocess
import threading
from pathlib  import Path
from datetime import datetime
from flask    import Flask, render_template, request, redirect, jsonify, Response, stream_with_context

BASE = Path(__file__).parent.parent   # carpeta /postulaciones
JOBS_FILE = BASE / "jobs.json"
CVS_DIR   = BASE / "cvs"
ENV_FILE  = BASE / ".env"

app = Flask(__name__)
output_lines = []   # buffer de output en vivo


def leer_env() -> dict:
    env = {}
    if ENV_FILE.exists():
        for line in ENV_FILE.read_text(encoding="utf-8").splitlines():
            if "=" in line and not line.startswith("#"):
                k, v = line.split("=", 1)
                env[k.strip()] = v.strip()
    return env


def guardar_env(data: dict) -> None:
    lineas = [f"{k}={v}" for k, v in data.items()]
    ENV_FILE.write_text("\n".join(lineas) + "\n", encoding="utf-8")


# ── Rutas ─────────────────────────────────────────────────────────────────────

@app.route("/")
def index():
    jobs = json.loads(JOBS_FILE.read_text(encoding="utf-8")) if JOBS_FILE.exists() else []
    cvs  = [f.name for f in CVS_DIR.iterdir()] if CVS_DIR.exists() else []
    enviadas  = sum(1 for j in jobs if j.get("enviado"))
    pendientes = sum(1 for j in jobs if not j.get("enviado"))
    return render_template("index.html", jobs=jobs, cvs=cvs,
                           enviadas=enviadas, pendientes=pendientes)


@app.route("/configurar", methods=["GET", "POST"])
def configurar():
    env = leer_env()
    msg = ""
    if request.method == "POST":
        env["ANTHROPIC_API_KEY"] = request.form.get("api_key", "").strip()
        guardar_env(env)
        # Guardar CV si se subió
        cv = request.files.get("cv")
        if cv and cv.filename:
            CVS_DIR.mkdir(exist_ok=True)
            cv.save(CVS_DIR / cv.filename)
        msg = "✓ Configuración guardada"
    return render_template("configurar.html", env=env, msg=msg)


@app.route("/agregar", methods=["POST"])
def agregar_job():
    jobs = json.loads(JOBS_FILE.read_text(encoding="utf-8")) if JOBS_FILE.exists() else []
    cvs  = [f.name for f in CVS_DIR.iterdir()] if CVS_DIR.exists() else []
    nuevo = {
        "empresa": request.form["empresa"],
        "rol":     request.form["rol"],
        "email":   request.form["email"],
        "cv":      request.form["cv"],
        "url":     request.form.get("url") or None,
        "enviado": False,
    }
    jobs.append(nuevo)
    JOBS_FILE.write_text(json.dumps(jobs, ensure_ascii=False, indent=2), encoding="utf-8")
    return redirect("/")


@app.route("/eliminar/<int:idx>")
def eliminar_job(idx):
    jobs = json.loads(JOBS_FILE.read_text(encoding="utf-8")) if JOBS_FILE.exists() else []
    if 0 <= idx < len(jobs):
        jobs.pop(idx)
        JOBS_FILE.write_text(json.dumps(jobs, ensure_ascii=False, indent=2), encoding="utf-8")
    return redirect("/")


@app.route("/correr")
def correr():
    return render_template("correr.html")


@app.route("/stream")
def stream():
    """Server-Sent Events: manda el output del script en tiempo real."""
    def generate():
        global output_lines
        output_lines = []

        scripts = [
            ("Postulando en portales...", ["python", str(BASE / "postular.py")]),
            ("Leyendo vacantes de Gmail...", ["python", str(BASE / "leer_vacantes.py")]),
            ("Generando cartas y borradores...", ["python", str(BASE / "main.py")]),
        ]

        for titulo, cmd in scripts:
            yield f"data: \n\n"
            yield f"data: === {titulo} ===\n\n"
            proc = subprocess.Popen(
                cmd, cwd=str(BASE),
                stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                text=True, encoding="utf-8", errors="replace"
            )
            for line in proc.stdout:
                line = line.rstrip()
                output_lines.append(line)
                yield f"data: {line}\n\n"
            proc.wait()

        yield "data: \n\n"
        yield "data: ✅ ¡Todo listo! Abrí Gmail → Borradores.\n\n"
        yield "data: [FIN]\n\n"

    return Response(stream_with_context(generate()),
                    mimetype="text/event-stream",
                    headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"})


if __name__ == "__main__":
    import webbrowser
    webbrowser.open("http://localhost:5000")
    app.run(debug=False, port=5000)
