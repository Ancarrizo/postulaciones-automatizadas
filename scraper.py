"""
Scraper de portales de empleo usando Playwright (navegador real, sin bloqueos).
Busca ofertas en Computrabajo, ZonaJobs y BumerAN según palabras clave del perfil.
"""

import time
import json
from pathlib import Path
from playwright.sync_api import sync_playwright, TimeoutError as PWTimeout

LEIDOS_FILE  = Path(__file__).parent / "vacantes_leidas.json"
JOBS_FILE    = Path(__file__).parent / "jobs.json"

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


def cargar_urls_vistas() -> set:
    if LEIDOS_FILE.exists():
        data = json.loads(LEIDOS_FILE.read_text(encoding="utf-8"))
        return set(data) if isinstance(data, list) else set()
    return set()


def guardar_urls_vistas(urls: set) -> None:
    LEIDOS_FILE.write_text(json.dumps(list(urls), ensure_ascii=False, indent=2), encoding="utf-8")


def ya_en_jobs(url: str) -> bool:
    if not JOBS_FILE.exists():
        return False
    jobs = json.loads(JOBS_FILE.read_text(encoding="utf-8"))
    return any(j.get("url") == url for j in jobs)


def agregar_a_jobs(titulo: str, empresa: str, url: str, fuente: str) -> None:
    jobs = json.loads(JOBS_FILE.read_text(encoding="utf-8")) if JOBS_FILE.exists() else []
    jobs.append({
        "empresa": empresa,
        "rol": titulo,
        "email": "",
        "cv": "CV_Andres_Carrizo_2026.docx",
        "url": url,
        "enviado": False,
        "origen": fuente,
    })
    JOBS_FILE.write_text(json.dumps(jobs, ensure_ascii=False, indent=2), encoding="utf-8")


# ── Computrabajo ─────────────────────────────────────────────────────────────

def scrape_computrabajo(page, keyword: str, vistas: set) -> list[dict]:
    resultados = []
    url = f"https://www.computrabajo.com.ar/trabajo-de-{keyword}"
    try:
        page.goto(url, wait_until="domcontentloaded", timeout=20000)
        page.wait_for_selector("article", timeout=10000)
    except PWTimeout:
        return resultados

    cards = page.query_selector_all("article")
    for card in cards:
        try:
            link = card.query_selector("h2 a, a.js-o-link")
            if not link:
                continue
            titulo = link.inner_text().strip()
            href   = link.get_attribute("href") or ""
            job_url = href if href.startswith("http") else "https://www.computrabajo.com.ar" + href
            if not titulo or job_url in vistas or ya_en_jobs(job_url):
                continue
            empresa_el = card.query_selector("[data-qa='COMPANY_NAME'], p.fs16")
            empresa = empresa_el.inner_text().strip() if empresa_el else "N/D"
            vistas.add(job_url)
            resultados.append({"titulo": titulo, "empresa": empresa, "url": job_url, "fuente": "Computrabajo"})
        except Exception:
            continue
    return resultados


# ── ZonaJobs ─────────────────────────────────────────────────────────────────

def scrape_zonajobs(page, keyword: str, vistas: set) -> list[dict]:
    resultados = []
    url = f"https://www.zonajobs.com.ar/empleos.html?q={keyword}"
    try:
        page.goto(url, wait_until="domcontentloaded", timeout=20000)
        page.wait_for_selector("article, [class*='aviso']", timeout=10000)
    except PWTimeout:
        return resultados

    cards = page.query_selector_all("article, [class*='AvisoContainer']")
    for card in cards:
        try:
            link = card.query_selector("a[href*='/empleo/'], h2 a, a")
            if not link:
                continue
            href    = link.get_attribute("href") or ""
            job_url = href if href.startswith("http") else "https://www.zonajobs.com.ar" + href
            if not href or job_url in vistas or ya_en_jobs(job_url):
                continue
            titulo_el = card.query_selector("h2, [class*='title']")
            titulo    = titulo_el.inner_text().strip() if titulo_el else link.inner_text().strip()
            empresa_el = card.query_selector("[class*='company'], [class*='empresa']")
            empresa    = empresa_el.inner_text().strip() if empresa_el else "N/D"
            if not titulo or len(titulo) < 4:
                continue
            vistas.add(job_url)
            resultados.append({"titulo": titulo, "empresa": empresa, "url": job_url, "fuente": "ZonaJobs"})
        except Exception:
            continue
    return resultados


# ── BumerAN ───────────────────────────────────────────────────────────────────

def scrape_bumeran(page, keyword: str, vistas: set) -> list[dict]:
    resultados = []
    url = f"https://www.bumeran.com.ar/empleos.html?q={keyword}"
    try:
        page.goto(url, wait_until="domcontentloaded", timeout=20000)
        page.wait_for_selector("a[href*='/empleos-'], article", timeout=10000)
    except PWTimeout:
        return resultados

    links = page.query_selector_all("a[href*='/empleos-']")
    vistas_href: set = set()
    for lnk in links:
        try:
            href    = lnk.get_attribute("href") or ""
            job_url = href if href.startswith("http") else "https://www.bumeran.com.ar" + href
            if job_url in vistas or job_url in vistas_href or ya_en_jobs(job_url):
                continue
            titulo = lnk.inner_text().strip()
            if not titulo or len(titulo) < 4:
                continue
            vistas_href.add(job_url)
            vistas.add(job_url)
            resultados.append({"titulo": titulo, "empresa": "N/D", "url": job_url, "fuente": "BumerAN"})
        except Exception:
            continue
    return resultados


# ── Función principal ─────────────────────────────────────────────────────────

def buscar_ofertas() -> list[dict]:
    """
    Busca ofertas nuevas en los 3 portales y las agrega a jobs.json.
    Retorna la lista de ofertas nuevas encontradas.
    """
    vistas   = cargar_urls_vistas()
    nuevas   = []

    print("Abriendo navegador...")
    with sync_playwright() as pw:
        browser = pw.chromium.launch(headless=True)
        ctx     = browser.new_context(user_agent=UA, locale="es-AR")
        page    = ctx.new_page()
        page.set_default_timeout(20000)

        for keyword in KEYWORDS:
            print(f"  Buscando: {keyword}")

            for fn, nombre in [
                (scrape_computrabajo, "Computrabajo"),
                (scrape_zonajobs,     "ZonaJobs"),
                (scrape_bumeran,      "BumerAN"),
            ]:
                try:
                    encontradas = fn(page, keyword, vistas)
                    for oferta in encontradas:
                        agregar_a_jobs(oferta["titulo"], oferta["empresa"], oferta["url"], oferta["fuente"])
                        nuevas.append(oferta)
                        print(f"    + [{oferta['fuente']}] {oferta['titulo']} — {oferta['empresa']}")
                    time.sleep(1.2)
                except Exception as e:
                    print(f"    [ERROR {nombre}] {e}")

        browser.close()

    guardar_urls_vistas(vistas)
    return nuevas


if __name__ == "__main__":
    print("=" * 55)
    print("  Scraping portales de empleo")
    print("=" * 55 + "\n")
    nuevas = buscar_ofertas()
    print(f"\n{'='*55}")
    print(f"  Ofertas nuevas encontradas: {len(nuevas)}")
    print(f"  Agregadas a jobs.json para procesar")
    print(f"{'='*55}")
