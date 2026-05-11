"""
Web app multi-usuario para postulaciones automatizadas.
Cada usuario carga su perfil y CV — las cartas se generan con sus datos.
Correr: python web/app.py
Abrir:  http://localhost:5000
"""

import os
import json
import anthropic
from pathlib import Path
from flask   import Flask, render_template, request, redirect, jsonify, session

BASE      = Path(__file__).parent.parent
CVS_DIR   = BASE / "cvs"
ENV_FILE  = BASE / ".env"

app = Flask(__name__)
app.secret_key = "postulaciones-secret-2026"   # para sesiones Flask


def get_api_key() -> str:
    if ENV_FILE.exists():
        for line in ENV_FILE.read_text(encoding="utf-8").splitlines():
            if line.startswith("ANTHROPIC_API_KEY="):
                return line.split("=", 1)[1].strip()
    return ""


# ── Rutas ─────────────────────────────────────────────────────────────────────

@app.route("/")
def index():
    perfil = session.get("perfil", {})
    return render_template("index.html", perfil=perfil)


@app.route("/perfil", methods=["GET", "POST"])
def perfil():
    msg = ""
    if request.method == "POST":
        # Guardar perfil en la sesión del navegador
        session["perfil"] = {
            "nombre":        request.form.get("nombre", "").strip(),
            "email":         request.form.get("email", "").strip(),
            "telefono":      request.form.get("telefono", "").strip(),
            "ubicacion":     request.form.get("ubicacion", "").strip(),
            "linkedin":      request.form.get("linkedin", "").strip(),
            "educacion":     request.form.get("educacion", "").strip(),
            "experiencia":   request.form.get("experiencia", "").strip(),
            "idiomas":       request.form.get("idiomas", "").strip(),
            "habilidades":   request.form.get("habilidades", "").strip(),
            "disponibilidad":request.form.get("disponibilidad", "").strip(),
            "pretension":    request.form.get("pretension", "").strip(),
        }

        # Guardar CV si se subió
        cv = request.files.get("cv")
        if cv and cv.filename:
            CVS_DIR.mkdir(exist_ok=True)
            cv_path = CVS_DIR / cv.filename
            cv.save(str(cv_path))
            session["cv_filename"] = cv.filename

        msg = "✓ Perfil guardado"

    perfil_actual = session.get("perfil", {})
    cv_actual     = session.get("cv_filename", "")
    return render_template("perfil.html", perfil=perfil_actual, cv=cv_actual, msg=msg)


@app.route("/generar", methods=["GET", "POST"])
def generar():
    perfil = session.get("perfil", {})
    if not perfil.get("nombre"):
        return redirect("/perfil")

    resultado = None
    error     = ""

    if request.method == "POST":
        empresa     = request.form.get("empresa", "").strip()
        rol         = request.form.get("rol", "").strip()
        descripcion = request.form.get("descripcion", "").strip()

        api_key = get_api_key()
        if not api_key:
            error = "Falta la API key de Anthropic. Contactá al administrador."
        else:
            try:
                from carta import generar_todo
                client    = anthropic.Anthropic(api_key=api_key)
                resultado = generar_todo(empresa, rol, descripcion, client, perfil)
                resultado["empresa"] = empresa
                resultado["rol"]     = rol
            except Exception as e:
                error = str(e)

    return render_template("generar.html", perfil=perfil, resultado=resultado, error=error)


if __name__ == "__main__":
    import webbrowser
    webbrowser.open("http://localhost:5000")
    app.run(debug=False, port=5000)
