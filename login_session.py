"""
Paso 1 (una sola vez): abre el navegador VISIBLE para que te logueés con Google
en cada portal. Guarda la sesión para que el bot no tenga que loguearse nunca más.

Correr: python login_session.py
"""

from playwright.sync_api import sync_playwright
from pathlib import Path

SESSIONS_DIR = Path(__file__).parent / "sessions"
SESSIONS_DIR.mkdir(exist_ok=True)

PORTALES = [
    {
        "nombre": "Computrabajo",
        "url":    "https://www.computrabajo.com.ar/login",
        "session": "session_computrabajo",
    },
    {
        "nombre": "ZonaJobs",
        "url":    "https://www.zonajobs.com.ar/login",
        "session": "session_zonajobs",
    },
    {
        "nombre": "BumerAN",
        "url":    "https://www.bumeran.com.ar/login",
        "session": "session_bumeran",
    },
]


def main():
    with sync_playwright() as pw:
        for portal in PORTALES:
            session_path = str(SESSIONS_DIR / portal["session"])
            print(f"\n{'='*50}")
            print(f"  {portal['nombre']}")
            print(f"{'='*50}")
            print(f"  1. Se abre el navegador")
            print(f"  2. Hacé clic en 'Ingresar con Google'")
            print(f"  3. Elegí Andicarrizo5@gmail.com")
            print(f"  4. Cuando estés logueado y veas tu perfil, cerrá el navegador")
            input(f"\n  Presioná ENTER para abrir {portal['nombre']}...")

            browser = pw.chromium.launch_persistent_context(
                user_data_dir=session_path,
                headless=False,          # visible para que te logueés
                locale="es-AR",
                viewport={"width": 1280, "height": 800},
            )
            page = browser.new_page()
            page.goto(portal["url"])

            print(f"\n  Esperando que cierres el navegador...")
            browser.wait_for_event("close", timeout=300000)   # 5 minutos máximo
            print(f"  ✓ Sesión de {portal['nombre']} guardada")

    print(f"\n{'='*50}")
    print(f"  ¡Listo! Las 3 sesiones están guardadas.")
    print(f"  Ya podés correr: python postular.py")
    print(f"{'='*50}")


if __name__ == "__main__":
    main()
