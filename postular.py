"""
Usa las sesiones guardadas para buscar ofertas y hacer clic en "Postularme"
automáticamente en Computrabajo, ZonaJobs y BumerAN.
"""

import time
import json
from pathlib import Path
from playwright.sync_api import sync_playwright, TimeoutError as PWTimeout

SESSIONS_DIR = Path(__file__).parent / "sessions"
JOBS_FILE    = Path(__file__).parent / "jobs.json"
LOG_FILE     = Path(__file__).parent / "borradores" / "postulaciones_portales.json"

KEYWORDS = [
    "comunicacion",
    "marketing",
    "recursos-humanos",
    "community-manager",
    "administracion",
    "ventas",
    "coordinador",
    "relaciones-publicas",
    "redaccion",
    "contenidos",
]

UA = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/124.0.0.0 Safari/537.36"
)


def cargar_log() -> list:
    if LOG_FILE.exists():
        return json.loads(LOG_FILE.read_text(encoding="utf-8"))
    return []


def guardar_log(log: list) -> None:
    LOG_FILE.parent.mkdir(exist_ok=True)
    LOG_FILE.write_text(json.dumps(log, ensure_ascii=False, indent=2), encoding="utf-8")


def ya_postulado(url: str, log: list) -> bool:
    return any(e.get("url") == url for e in log)


# ── Computrabajo ──────────────────────────────────────────────────────────────

def postular_computrabajo(keyword: str, log: list) -> list:
    nuevas = []
    session_path = str(SESSIONS_DIR / "session_computrabajo")
    if not Path(session_path).exists():
        print("  [!] No hay sesión de Computrabajo. Corré login_session.py primero.")
        return []

    with sync_playwright() as pw:
        browser = pw.chromium.launch_persistent_context(
            user_data_dir=session_path,
            headless=True,
            locale="es-AR",
        )
        page = browser.new_page()

        try:
            page.goto(f"https://www.computrabajo.com.ar/trabajo-de-{keyword}", timeout=20000)
            page.wait_for_selector("article", timeout=10000)
        except PWTimeout:
            browser.close()
            return []

        cards = page.query_selector_all("article")
        for card in cards[:10]:   # máximo 10 por keyword
            try:
                link = card.query_selector("h2 a, a.js-o-link")
                if not link:
                    continue
                titulo  = link.inner_text().strip()
                href    = link.get_attribute("href") or ""
                job_url = href if href.startswith("http") else "https://www.computrabajo.com.ar" + href

                if ya_postulado(job_url, log):
                    continue

                empresa_el = card.query_selector("[data-qa='COMPANY_NAME'], p.fs16")
                empresa    = empresa_el.inner_text().strip() if empresa_el else "N/D"

                # Abrir la oferta
                page.goto(job_url, timeout=15000)
                time.sleep(1.5)

                # Buscar botón de postulación
                btn = page.query_selector(
                    "button:has-text('Postularme'), a:has-text('Postularme'), "
                    "button:has-text('Aplicar'), [data-qa='BTN_APPLY']"
                )
                if btn:
                    btn.click()
                    time.sleep(2)

                    # Confirmar si hay popup
                    confirmar = page.query_selector(
                        "button:has-text('Confirmar'), button:has-text('Enviar'), "
                        "button:has-text('Postularme')"
                    )
                    if confirmar:
                        confirmar.click()
                        time.sleep(1.5)

                    print(f"    ✓ Postulado: {titulo} — {empresa}")
                    log.append({"portal": "Computrabajo", "titulo": titulo, "empresa": empresa, "url": job_url})
                    nuevas.append({"titulo": titulo, "empresa": empresa, "url": job_url})
                else:
                    print(f"    – Sin botón: {titulo}")

                time.sleep(1.5)

            except Exception as e:
                print(f"    [ERROR] {e}")
                continue

        browser.close()

    return nuevas


# ── ZonaJobs ─────────────────────────────────────────────────────────────────

def postular_zonajobs(keyword: str, log: list) -> list:
    nuevas = []
    session_path = str(SESSIONS_DIR / "session_zonajobs")
    if not Path(session_path).exists():
        print("  [!] No hay sesión de ZonaJobs. Corré login_session.py primero.")
        return []

    with sync_playwright() as pw:
        browser = pw.chromium.launch_persistent_context(
            user_data_dir=session_path,
            headless=True,
            locale="es-AR",
        )
        page = browser.new_page()

        try:
            page.goto(f"https://www.zonajobs.com.ar/empleos.html?q={keyword}", timeout=20000)
            page.wait_for_selector("article, [class*='aviso']", timeout=10000)
        except PWTimeout:
            browser.close()
            return []

        links = page.query_selector_all("a[href*='/empleo/']")
        hrefs_vistos: set = set()

        for lnk in links[:10]:
            try:
                href    = lnk.get_attribute("href") or ""
                job_url = href if href.startswith("http") else "https://www.zonajobs.com.ar" + href
                if not href or job_url in hrefs_vistos or ya_postulado(job_url, log):
                    continue
                hrefs_vistos.add(job_url)

                page.goto(job_url, timeout=15000)
                time.sleep(1.5)

                titulo_el = page.query_selector("h1")
                titulo    = titulo_el.inner_text().strip() if titulo_el else href

                btn = page.query_selector(
                    "button:has-text('Postularme'), a:has-text('Postularme'), "
                    "button:has-text('Aplicar')"
                )
                if btn:
                    btn.click()
                    time.sleep(2)
                    confirmar = page.query_selector("button:has-text('Confirmar'), button:has-text('Enviar')")
                    if confirmar:
                        confirmar.click()
                        time.sleep(1.5)
                    print(f"    ✓ Postulado: {titulo}")
                    log.append({"portal": "ZonaJobs", "titulo": titulo, "empresa": "N/D", "url": job_url})
                    nuevas.append({"titulo": titulo, "empresa": "N/D", "url": job_url})
                else:
                    print(f"    – Sin botón: {titulo}")

                time.sleep(1.5)

            except Exception as e:
                print(f"    [ERROR] {e}")
                continue

        browser.close()

    return nuevas


# ── BumerAN ───────────────────────────────────────────────────────────────────

def postular_bumeran(keyword: str, log: list) -> list:
    nuevas = []
    session_path = str(SESSIONS_DIR / "session_bumeran")
    if not Path(session_path).exists():
        print("  [!] No hay sesión de BumerAN. Corré login_session.py primero.")
        return []

    with sync_playwright() as pw:
        browser = pw.chromium.launch_persistent_context(
            user_data_dir=session_path,
            headless=True,
            locale="es-AR",
        )
        page = browser.new_page()

        try:
            page.goto(f"https://www.bumeran.com.ar/empleos.html?q={keyword}", timeout=20000)
            page.wait_for_selector("a[href*='/empleos-']", timeout=10000)
        except PWTimeout:
            browser.close()
            return []

        links = page.query_selector_all("a[href*='/empleos-']")
        hrefs_vistos: set = set()

        for lnk in links[:10]:
            try:
                href    = lnk.get_attribute("href") or ""
                job_url = href if href.startswith("http") else "https://www.bumeran.com.ar" + href
                if not href or job_url in hrefs_vistos or ya_postulado(job_url, log):
                    continue
                hrefs_vistos.add(job_url)

                titulo = lnk.inner_text().strip()
                if not titulo or len(titulo) < 4:
                    continue

                page.goto(job_url, timeout=15000)
                time.sleep(1.5)

                btn = page.query_selector(
                    "button:has-text('Postularme'), a:has-text('Postularme'), "
                    "button:has-text('Aplicar')"
                )
                if btn:
                    btn.click()
                    time.sleep(2)
                    confirmar = page.query_selector("button:has-text('Confirmar'), button:has-text('Enviar')")
                    if confirmar:
                        confirmar.click()
                        time.sleep(1.5)
                    print(f"    ✓ Postulado: {titulo}")
                    log.append({"portal": "BumerAN", "titulo": titulo, "empresa": "N/D", "url": job_url})
                    nuevas.append({"titulo": titulo, "empresa": "N/D", "url": job_url})
                else:
                    print(f"    – Sin botón: {titulo}")

                time.sleep(1.5)

            except Exception as e:
                print(f"    [ERROR] {e}")
                continue

        browser.close()

    return nuevas


# ── Principal ─────────────────────────────────────────────────────────────────

def postular_en_portales() -> None:
    log    = cargar_log()
    total  = 0

    print("=" * 55)
    print("  Postulando en portales con Playwright")
    print("=" * 55)

    for keyword in KEYWORDS:
        print(f"\n[{keyword}]")

        for fn, nombre in [
            (postular_computrabajo, "Computrabajo"),
            (postular_zonajobs,     "ZonaJobs"),
            (postular_bumeran,      "BumerAN"),
        ]:
            nuevas = fn(keyword, log)
            total += len(nuevas)

    guardar_log(log)

    print(f"\n{'='*55}")
    print(f"  Postulaciones realizadas hoy: {total}")
    print(f"  Log guardado en: borradores/postulaciones_portales.json")
    print(f"{'='*55}")


if __name__ == "__main__":
    postular_en_portales()
