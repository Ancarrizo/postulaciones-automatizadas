"""
Generador de cartas + keywords + resumen profesional adaptado.
Acepta cualquier perfil dinámico — multi-usuario.
"""

import json
import anthropic

SYSTEM_TEMPLATE = """Sos un experto en Recursos Humanos y comunicación profesional argentina con 15 años de experiencia.

PERFIL DEL CANDIDATO:
{perfil}

Tu tarea es analizar la oferta laboral y producir tres cosas en formato JSON:

1. "keywords": lista de 5-8 palabras o frases clave de la oferta que el candidato cumple
2. "resumen": párrafo de 2-3 líneas para el encabezado del CV, adaptado a esta oferta.
   Natural, en primera persona, sin clichés, destacando lo más relevante para ESE puesto.
3. "carta": carta de presentación. Máximo 3 párrafos cortos. Tono humano, directo,
   español rioplatense. Sin "soy proactivo", "me apasiona", "me considero".
   Usá logros concretos del perfil. Último párrafo: cierre que invite a entrevista. Sin firma.

Respondé SOLO con JSON válido, sin markdown, con exactamente estas tres claves: keywords, resumen, carta.
"""

FIRMA_TEMPLATE = (
    "\n\nQuedo a disposición ante cualquier consulta.\n\n"
    "{nombre}\n"
    "{telefono} | {email}\n"
    "{linkedin}"
)


def construir_perfil_texto(perfil: dict) -> str:
    """Convierte el dict de perfil en texto para el prompt."""
    lineas = [
        f"Nombre: {perfil.get('nombre', '')}",
        f"Ubicación: {perfil.get('ubicacion', '')}",
        f"Email: {perfil.get('email', '')}",
    ]
    if perfil.get("linkedin"):
        lineas.append(f"LinkedIn: {perfil['linkedin']}")
    if perfil.get("educacion"):
        lineas.append(f"Educación: {perfil['educacion']}")
    if perfil.get("experiencia"):
        lineas.append(f"Experiencia:\n{perfil['experiencia']}")
    if perfil.get("idiomas"):
        lineas.append(f"Idiomas: {perfil['idiomas']}")
    if perfil.get("habilidades"):
        lineas.append(f"Habilidades: {perfil['habilidades']}")
    if perfil.get("disponibilidad"):
        lineas.append(f"Disponibilidad: {perfil['disponibilidad']}")
    if perfil.get("pretension"):
        lineas.append(f"Pretensión salarial: {perfil['pretension']}")
    return "\n".join(lineas)


def generar_todo(empresa: str, rol: str, descripcion: str,
                 client: anthropic.Anthropic, perfil: dict) -> dict:
    """
    Genera carta + keywords + resumen para cualquier perfil.
    """
    perfil_texto = construir_perfil_texto(perfil)
    system = SYSTEM_TEMPLATE.format(perfil=perfil_texto)

    prompt = (
        f"OFERTA:\n"
        f"Empresa: {empresa}\n"
        f"Puesto: {rol}\n"
        f"Descripción: {descripcion or 'No disponible'}\n\n"
        f"Generá el JSON con keywords, resumen y carta para esta postulación."
    )

    resp = client.messages.create(
        model="claude-sonnet-4-5",
        max_tokens=1000,
        system=[{"type": "text", "text": system, "cache_control": {"type": "ephemeral"}}],
        messages=[{"role": "user", "content": prompt}],
    )

    try:
        data = json.loads(resp.content[0].text.strip())
    except Exception:
        data = {
            "keywords": [],
            "resumen": f"Profesional con experiencia en {rol}.",
            "carta": resp.content[0].text.strip(),
        }

    # Firma dinámica con datos del perfil
    firma = FIRMA_TEMPLATE.format(
        nombre   = perfil.get("nombre", ""),
        telefono = perfil.get("telefono", ""),
        email    = perfil.get("email", ""),
        linkedin = perfil.get("linkedin", ""),
    )
    data["carta"] = data.get("carta", "").strip() + firma
    return data


def generar_carta(empresa: str, rol: str, client: anthropic.Anthropic,
                  descripcion: str = "", perfil: dict = None) -> str:
    """Compatibilidad con código existente."""
    perfil = perfil or {}
    return generar_todo(empresa, rol, descripcion, client, perfil)["carta"]
