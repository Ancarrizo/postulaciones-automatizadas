"""
Generador de cartas + análisis de keywords + resumen profesional adaptado.
Todo en una sola llamada cacheada a Claude.
"""

import json
import anthropic

PERFIL = """
Andrés Carrizo, 26 años, La Plata, Buenos Aires.
- Licenciado en Comunicación Social, UNLP 2026, orientación Planificación. Promedio 8.7/10.
- Co-fundador de CaSa Comunicación: agencia propia con clientes activos en educación, gastronomía y cosmetología.
- Ventas / Marketing / Logística en Rodar Electric SRL (abril 2025 - actualidad): CRM, +50 prospectos diarios, logística end-to-end.
- Asistente de Comunicación en Input Gym (2023).
- 5 años en atención al cliente en Agencia de Lotería (2019-2024).
- Idiomas: inglés intermedio-alto (B2), francés DELF A2 certificado, portugués intermedio.
- Herramientas: Microsoft Office avanzado, CRM, Adobe Photoshop, Premiere, HTML/CSS.
- Habilidades: redacción institucional, copywriting, estrategia de contenidos, gestión de equipos, KPIs.
- Disponibilidad inmediata. Pretensión: $1.800.000 ARS bruto.
""".strip()

SYSTEM = f"""Sos un experto en Recursos Humanos y comunicación profesional argentina con 15 años de experiencia
seleccionando candidatos y redactando postulaciones exitosas.

PERFIL DEL CANDIDATO:
{PERFIL}

Tu tarea es analizar cada oferta laboral y producir tres cosas en formato JSON:

1. "keywords": lista de 5-8 palabras o frases clave de la oferta que el candidato cumple
2. "resumen": párrafo de 2-3 líneas para el encabezado del CV, adaptado a esta oferta específica.
   Debe sonar natural, destacar lo más relevante para ESE puesto, en primera persona, sin clichés.
3. "carta": carta de presentación completa. Máximo 3 párrafos cortos. Tono humano y directo,
   español rioplatense. Sin frases como "soy proactivo", "me apasiona", "me considero".
   Usá logros concretos. Último párrafo: cierre que invite a entrevista. Sin firma.

Respondé SOLO con JSON válido, sin markdown, con exactamente estas tres claves: keywords, resumen, carta.
"""

FIRMA = (
    "\n\nQuedo a disposición ante cualquier consulta.\n\n"
    "Andrés Carrizo\n"
    "+54 221 502-6532 | Andicarrizo5@gmail.com\n"
    "linkedin.com/in/andressalvadorcarrizo"
)


def generar_todo(empresa: str, rol: str, descripcion: str, client: anthropic.Anthropic) -> dict:
    """
    Genera en una sola llamada:
    - keywords relevantes de la oferta
    - resumen profesional adaptado para el CV
    - carta de presentación personalizada

    Retorna dict con claves: keywords, resumen, carta
    """
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
        system=[
            {
                "type": "text",
                "text": SYSTEM,
                "cache_control": {"type": "ephemeral"},  # perfil cacheado
            }
        ],
        messages=[{"role": "user", "content": prompt}],
    )

    try:
        data = json.loads(resp.content[0].text.strip())
    except Exception:
        # fallback si el JSON viene mal
        data = {
            "keywords": [],
            "resumen": f"Licenciado en Comunicación Social con experiencia en {rol}.",
            "carta": resp.content[0].text.strip(),
        }

    # Agregar firma a la carta
    data["carta"] = data.get("carta", "").strip() + FIRMA
    return data


def generar_carta(empresa: str, rol: str, client: anthropic.Anthropic, descripcion: str = "") -> str:
    """Compatibilidad con el código existente — retorna solo la carta."""
    return generar_todo(empresa, rol, descripcion, client)["carta"]
