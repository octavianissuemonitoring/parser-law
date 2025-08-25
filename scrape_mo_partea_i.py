import hashlib
import json
import requests
import time
import logging
import os
import re
import pandas as pd
import csv
import html
import unicodedata
import hashlib
import json
import requests
import time
import logging
import os
import re
import pandas as pd
import csv
import html
import unicodedata
from pathlib import Path
from typing import Dict, List, Tuple, Optional, Any
from tqdm import tqdm
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse
from playwright.sync_api import sync_playwright
# Pentru extragerea textului din PDF
try:
    from pdfminer.high_level import extract_text
except ImportError:
    def extract_text(pdf_path):
        return "PDF text extraction not available"

# ------------------- CONFIG -------------------
START_URL = "https://monitoruloficial.ro/acte-publicate-in-monitorul-oficial-partea-i/"
MAX_ITEMS = 30
OUTPUT_DIR = Path("mo_partea_i_pdfs")   # folderul cu PDF-urile descărcate
OUTPUT_CSV = Path("mo_partea_i_last30.csv")
TIMEOUT_MS = 30000

# Heuristici pentru găsirea containerului unui link PDF (căutăm heading + text în preajmă)
HEADING_TAGS = ("h1", "h2", "h3", "h4", "h5", "h6")

# Regex pt. dată și emitent (ajustează dacă observi alte tipare)
DATE_PATTERNS = [
    r"\b(\d{1,2}\.\d{1,2}\.\d{4})\b",                     # 12.08.2025
    r"\b(\d{1,2}\s+[a-zA-ZăîâșțĂÎÂȘȚ]+\.?\s+\d{4})\b",    # 12 august 2025
]
EMITENT_PATTERNS = [
    r"(?:Emitent|Autoritatea\s+emitent[ăa]|EMITENT)\s*[:\-–]\s*([^\n|•]+)",
]

# configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s: %(message)s",
)
logger = logging.getLogger("mo_scraper")

# --------------------------------------------------------

def sanitize_filename(name: str, max_len: int = 120) -> str:
    name = re.sub(r"[^\w\-. ]+", "_", name, flags=re.UNICODE)
    name = re.sub(r"\s+", " ", name).strip()
    if len(name) > max_len:
        name = name[:max_len].rstrip()
    return name or "document"

def ensure_dir(path: Path):
    path.mkdir(parents=True, exist_ok=True)

def find_nearest_heading(block: BeautifulSoup) -> str:
    # caută heading în block
    for tag in block.find_all(HEADING_TAGS):
        txt = tag.get_text(" ", strip=True)
        if txt:
            return txt
    # dacă nu există heading, ia primul <a> cu text lung sau textul blocului
    long_links = [a.get_text(" ", strip=True) for a in block.find_all("a")]
    long_links = [t for t in long_links if len(t) >= 10]
    if long_links:
        return long_links[0]
    return block.get_text(" ", strip=True)[:140]

def extract_authority(text_block: str) -> Optional[str]:
    for pat in EMITENT_PATTERNS:
        m = re.search(pat, text_block, flags=re.IGNORECASE)
        if m:
            val = m.group(1).strip(" :–-")
            return re.sub(r"\s{2,}", " ", val)
    # alte indicii (Guvernul, Parlamentul, Ministerul …)
    m2 = re.search(r"\b(Guvernul României|Parlamentul României|Camera Deputaților|Senatul României|Președintele României|Ministerul [^,;|]+)", text_block, flags=re.IGNORECASE)
    if m2:
        return m2.group(1)
    return None

def extract_date(text_block: str) -> Optional[str]:
    for pat in DATE_PATTERNS:
        m = re.search(pat, text_block, flags=re.IGNORECASE)
        if m:
            return m.group(1)
    # uneori apare „din 12.08.2025”
    m2 = re.search(r"\bdin\s+(\d{1,2}\.\d{1,2}\.\d{4})\b", text_block, flags=re.IGNORECASE)
    if m2:
        return m2.group(1)
    return None

def build_absolute_url(base: str, href: str) -> str:
    return urljoin(base, href)

def guess_filename_from_url(pdf_url: str) -> str:
    path = urlparse(pdf_url).path
    base = os.path.basename(path) or "document.pdf"
    if not base.lower().endswith(".pdf"):
        base += ".pdf"
    return base

def download_pdf(pdf_url: str, target_dir: Path, session: requests.Session, retries: int = 3, backoff: float = 1.0) -> Path:
    """
    Descarcă PDF cu retry și validare Content-Type / magic bytes.
    Ridică excepție dacă după toate încercările nu s-a obținut un PDF valid.
    """
    ensure_dir(target_dir)
    fname = sanitize_filename(guess_filename_from_url(pdf_url))
    target = target_dir / fname
    # dacă există deja, adaugă hash scurt
    if target.exists():
        h = hashlib.sha1(pdf_url.encode("utf-8")).hexdigest()[:8]
        target = target_dir / f"{target.stem}_{h}{target.suffix}"

    last_err: Any = None
    for attempt in range(1, retries + 1):
        r = None
        try:
            logger.info("Descărc: %s (încercarea %d/%d)", pdf_url, attempt, retries)
            r = session.get(pdf_url, stream=True, timeout=60)
            r.raise_for_status()
            ct = r.headers.get("Content-Type", "").lower()
            iterator = r.iter_content(chunk_size=65536)
            try:
                first_chunk = next(iterator)
            except StopIteration:
                first_chunk = b""

            # verificare Content-Type sau magic bytes '%PDF'
            if "pdf" not in ct and not first_chunk.startswith(b"%PDF"):
                raise ValueError(f"Conținut neașteptat (Content-Type={ct}) și magic bytes absent")

            with open(target, "wb") as f:
                if first_chunk:
                    f.write(first_chunk)
                for chunk in iterator:
                    if chunk:
                        f.write(chunk)

            logger.info("Salvat: %s -> %s", pdf_url, target)
            return target

        except Exception as e:
            last_err = e
            logger.warning("Eroare descărcare (%s): %s", pdf_url, e)
            if attempt < retries:
                sleep_time = backoff * (2 ** (attempt - 1))
                logger.info("Retry în %.1f sec...", sleep_time)
                time.sleep(sleep_time)
            else:
                logger.error("Eșuat după %d încercări: %s", retries, pdf_url)

        finally:
            try:
                if r is not None:
                    r.close()
            except Exception:
                pass

    # la eșec, propagăm ultima eroare
    raise last_err

def extract_pdf_text(pdf_path: Path) -> str:
    try:
        text = extract_text(pdf_path)
        text = re.sub(r"\s+\n", "\n", text)
        return text.strip()
    except Exception:
        return ""

def _atomic_save_df(df: pd.DataFrame, path: Path):
    tmp = path.with_suffix(".tmp")
    df.to_csv(tmp, index=False, quoting=csv.QUOTE_ALL)
    os.replace(str(tmp), str(path))

# Adaugă dicționarul pentru convertirea lunilor în română
MONTH_NAMES_RO = {
    'ianuarie': '01', 'februarie': '02', 'martie': '03', 'aprilie': '04', 'mai': '05', 'iunie': '06',
    'iulie': '07', 'august': '08', 'septembrie': '09', 'octombrie': '10', 'noiembrie': '11', 'decembrie': '12',
    'ian': '01', 'feb': '02', 'mar': '03', 'apr': '04', 'iun': '06', 'iul': '07', 'aug': '08', 'sept': '09', 
    'sep': '09', 'oct': '10', 'noi': '11', 'nov': '11', 'dec': '12'
}

def normalize_romanian_text(text: str) -> str:
    """Normalizează textul român cu diacritice pentru afișare corectă."""
    if not text:
        return ""
    
    # Decodifică entitățile HTML
    text = html.unescape(text)
    
    # Normalizează Unicode (transformă caracterele compuse în precompuse)
    text = unicodedata.normalize('NFC', text)
    
    # Fix pentru codificări comune greșite ale diacriticelor
    replacements = {
        'Ã¢': 'â', 'Ã®': 'î', 'ÅŸ': 'ș', 'Å£': 'ț', 'Äƒ': 'ă',
        'Ã‚': 'Â', 'ÃŽ': 'Î', 'Åž': 'Ș', 'Ĺš': 'Ț', 'Ä‚': 'Ă',
        'È™': 'ș', 'È›': 'ț', 'ÎŁ': 'Ș', 'Τ': 'Ț',
        'Å±': 'ț', 'Å£': 'ț'
    }
    
    for wrong, correct in replacements.items():
        text = text.replace(wrong, correct)
    
    return text

def normalize_date_format(date_str: str) -> str:
    """Convertește diverse formate de dată la standardul DD.MM.YYYY"""
    if not date_str:
        return ""
    
    # Dacă data este deja în formatul DD.MM.YYYY
    if re.match(r'^\d{1,2}\.\d{1,2}\.\d{4}$', date_str):
        parts = date_str.split('.')
        day = parts[0].zfill(2)  # asigură că ziua are 2 cifre
        month = parts[1].zfill(2)  # asigură că luna are 2 cifre
        return f"{day}.{month}.{parts[2]}"
    
    # Pentru formatul "12 august 2025"
    match = re.match(r'(\d{1,2})\s+([a-zA-ZăîâșțĂÎÂȘȚ]+)\.?\s+(\d{4})', date_str)
    if match:
        day = match.group(1).zfill(2)
        month_name_ro = match.group(2).lower().rstrip('.')
        year = match.group(3)
        
        # Convertim numele lunii în număr
        if month_name_ro in MONTH_NAMES_RO:
            month = MONTH_NAMES_RO[month_name_ro]
            return f"{day}.{month}.{year}"
    
    # Nu s-a putut converti, returnăm așa cum este
    return date_str

# Înlocuiește funcția extract_date_from_parnr cu versiunea actualizată
def extract_date_from_parnr(parnr_text: str) -> str:
    """Extrage data din textul parnr și o convertește la formatul DD.MM.YYYY"""
    m = re.search(r"(\d{1,2}\s+[A-Za-zăîâșțĂÎÂȘȚ]+\.?\s+\d{4})", parnr_text)
    if m:
        return normalize_date_format(m.group(1).strip())
    m2 = re.search(r"(\d{1,2}\.\d{1,2}\.\d{4})", parnr_text)
    if m2:
        return normalize_date_format(m2.group(1))
    return ""

def scrape_metadata_stage() -> pd.DataFrame:
    """
    Extrage metadatele din primele 3 pagini.
    - Utilizează verificare primară și secundară pentru a asigura extragerea completă
    - Navighează prin paginare vizibilă (1, 2, 3) conform interfaței
    """
    logger.info("METADATA STAGE: start (pages 1..3)")
    rows: list[dict[str, str]] = []
    seen: set[str] = set()
    page_htmls: list[str] = []  # stocăm HTML pt. fallback
    page_counts: list[int] = [] # numărăm elemente per pagină

    # --- helperi interni (presupun existența regex / funcții auxiliare definite anterior) ---
    def extract_number_from_parnr(parnr_text: str) -> str:
        m = re.search(r"Nr\.?\s*([0-9]{2,5})\s*(?:/|$)", parnr_text, flags=re.IGNORECASE)
        if m:
            return m.group(1)
        m2 = re.search(r"\b([0-9]{2,5})\b", parnr_text)
        return m2.group(1) if m2 else ""

    def extract_date_from_parnr(parnr_text: str) -> str:
        m = re.search(r"(\d{1,2}\s+[A-Za-zăîâșțĂÎÂȘȚ]+\.?\s+\d{4})", parnr_text)
        if m:
            return m.group(1).strip()
        m2 = re.search(r"(\d{1,2}\.\d{1,2}\.\d{4})", parnr_text)
        return m2.group(1) if m2 else ""

    def extract_authority_from_parnr(parnr_text: str) -> str:
        # euristic: după ultima virgulă sau după slash / text final
        if "," in parnr_text:
            cand = parnr_text.rsplit(",", 1)[-1].strip()
            if len(cand) >= 3:
                return normalize_romanian_text(cand)
        parts = re.split(r"/", parnr_text)
        tail = parts[-1].strip()
        return normalize_romanian_text(tail)

    def clean_monitor_text(p_parmo_tag) -> str:
        if not p_parmo_tag:
            return ""
        # Creăm o copie a elementului pentru a nu modifica originalul
        tmp = BeautifulSoup(str(p_parmo_tag), "html.parser")
        # Extragem primul element (care va fi <p class="parmo">)
        p_copy = tmp.find("p")
        if not p_copy:
            return normalize_romanian_text(p_parmo_tag.get_text(" ", strip=True))
        # Eliminăm linkurile
        for a in p_copy.find_all("a"):
            a.extract()
        txt = p_copy.get_text(" ", strip=True)
        return normalize_romanian_text(re.sub(r"\s+", " ", txt).strip())

    primary_total = 0

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(locale="ro-RO")
        page = context.new_page()
        page.set_default_timeout(TIMEOUT_MS)

        page.goto(START_URL, wait_until="domcontentloaded", timeout=120_000)
        logger.info("S-a încărcat pagina inițială: %s", START_URL)

        # încercare înlăturare cookie banners
        for selector in [
            "button:has-text('Accept')",
            "button:has-text('De acord')",
            "button:has-text('Sunt de acord')",
            "button:has-text('OK')",
            "div[role=dialog] button:has-text('Accept')",
        ]:
            try:
                btn = page.locator(selector).first()
                if btn and btn.is_visible():
                    btn.click()
                    logger.info("S-a închis bannerul de cookie")
                    break
            except Exception:
                pass

        # Parsare pagina 1 (suntem deja pe ea)
        logger.info("Procesez pagina 1...")
        
        # Verifică dacă suntem pe pagina 1 și asigură-te că este activă
        try:
            page.wait_for_selector('.pagination', timeout=10000)
            # Click explicit pe pagina 1 pentru a asigura că suntem acolo
            if page.locator('.pagination .page-link:text("1")').count() > 0:
                page.click('.pagination .page-link:text("1")')
                logger.info("Click explicit pe pagina 1 pentru a o activa")
                page.wait_for_timeout(2000)
        except Exception as e:
            logger.warning(f"Nu am putut verifica/activa pagina 1: {e}")
        
        # Așteaptă mai mult pentru încărcarea completă a conținutului
        try:
            # Încearcă mai multe selectori posibile pentru containerul cu inițiative
            for selector in [
                'div.table-responsive#dynamic_content', 
                'div.table-responsive', 
                '#ajax_content div.table-responsive',
                '.mo1-item'  # un posibil selector alternativ pentru elemente
            ]:
                try:
                    found = page.wait_for_selector(selector, timeout=15000)
                    if found:
                        logger.info(f"Pagina 1: Am găsit containerul cu selector {selector}")
                        break
                except Exception:
                    pass
                    
            # Așteaptă mai mult timp să se încarce tot conținutul
            page.wait_for_timeout(3000)
            
            # Așteaptă explicit să apară p.paraar
            try:
                p_count = page.locator('p.paraar').count()
                logger.info(f"Pagina 1: {p_count} paragrafe .paraar găsite direct în DOM")
            except Exception:
                pass
                
        except Exception as e:
            logger.warning(f"Așteptare încărcare pagina 1 a eșuat: {e}")

        # Facem screenshot pentru debug
        try:
            screenshot_path = "pagina1_debug.png"
            page.screenshot(path=screenshot_path)
            logger.info(f"Screenshot salvat pentru debug la: {screenshot_path}")
        except Exception as e:
            logger.warning(f"Nu am putut salva screenshot: {e}")

        html = page.content()
        page_htmls.append(html)
        
        # Verificăm DOM-ul pentru a diagnostica problema
        logger.info("Analizez structura HTML pagina 1...")
        soup = BeautifulSoup(html, "html.parser")
        
        # Caută containerul folosind mai mulți selectori
        target_div = None
        for selector in [
            "div.table-responsive#dynamic_content", 
            "div.table-responsive", 
            "#ajax_content div.table-responsive",
            ".dataTables_wrapper"
        ]:
            found = soup.select_one(selector)
            if found:
                target_div = found
                logger.info(f"Pagina 1: Am găsit container cu selector '{selector}'")
                break
                
        if target_div:
            # Verifică alte elemente pentru a înțelege structura paginii
            all_divs = len(soup.find_all("div"))
            all_p = len(soup.find_all("p"))
            logger.info(f"Pagina 1 DOM: {all_divs} div-uri, {all_p} paragrafe în total")
            
            # Verifică în tot DOM-ul pentru paragrafe relevante
            all_paraar = soup.find_all("p", class_="paraar")
            if all_paraar:
                logger.info(f"Pagina 1: Am găsit {len(all_paraar)} paragrafe paraar în tot DOM-ul")
                
                # Folosește aceste paragrafe direct din tot DOM-ul dacă nu există în container
                paraar_tags = target_div.find_all("p", class_="paraar")
                if not paraar_tags:
                    logger.warning("Paragrafe găsite în DOM dar nu în container - folosesc paragrafe din tot DOM-ul")
                    paraar_tags = all_paraar
            else:
                logger.warning("Nu există paragrafe paraar în DOM - posibil nume clasă diferit sau structură diferită")
                # Încearcă să găsească paragrafe cu alt conținut relevant
                candidate_p = [p for p in soup.find_all("p") if len(p.get_text(strip=True)) > 50]
                if candidate_p:
                    logger.info(f"Am găsit {len(candidate_p)} paragrafe candidate (text > 50 caractere)")
                    paraar_tags = candidate_p
                else:
                    paraar_tags = []
                    
            page_counts.append(len(paraar_tags))
            primary_total += len(paraar_tags)
            logger.info("Pagina 1: %d inițiative găsite", len(paraar_tags))
            
            # Procesează inițiativele găsite
            for p_paraar in paraar_tags:
                parent_div = p_paraar.find_parent("div")
                if not parent_div:
                    continue

                title = p_paraar.get_text(" ", strip=True)
                if not title:
                    continue
                
                # Găsește p.parmo și p.parnr fie în același părinte, fie în apropiere
                p_parmo = parent_div.find("p", class_="parmo")
                p_parnr = parent_div.find("p", class_="parnr")
                
                # Fallback: caută în frații (siblings) paragrafului curent
                if not p_parmo:
                    p_parmo = p_paraar.find_next_sibling("p", class_="parmo")
                if not p_parnr:
                    p_parnr = p_paraar.find_next_sibling("p", class_="parnr")
                
                monitor_info = clean_monitor_text(p_parmo)
                parnr_text = p_parnr.get_text(" ", strip=True) if p_parnr else ""

                # Restul procesării rămâne neschimbat
                numar = extract_number_from_parnr(parnr_text)
                data = extract_date_from_parnr(parnr_text)
                authority = extract_authority_from_parnr(parnr_text)

                if not any([title.strip(), numar.strip(), data.strip(), authority.strip(), monitor_info.strip()]):
                    continue

                key = f"{title}|{numar}|{monitor_info}"
                if key in seen:
                    continue
                seen.add(key)

                rows.append({
                    "title": normalize_romanian_text(title),
                    "numar": numar,
                    "data": normalize_date_format(data),
                    "authority": normalize_romanian_text(authority),
                    "monitor": normalize_romanian_text(monitor_info)
                })
        else:
            logger.error("Nu am putut găsi niciun container valid pentru pagina 1")
            # Încearcă un fallback radical - ia toate paragrafele din pagină
            all_p = soup.find_all("p")
            long_p = [p for p in all_p if len(p.get_text(strip=True)) > 50]
            logger.info(f"Fallback pagina 1: {len(long_p)} paragrafe lungi găsite în tot documentul")
            for p_paraar in long_p:
                title = p_paraar.get_text(" ", strip=True)
                if not title:
                    continue
                
                # Fallback pentru p_parmo și p_parnr - caută în frații (siblings) paragrafului curent
                p_parmo = p_paraar.find_next_sibling("p", class_="parmo")
                p_parnr = p_paraar.find_next_sibling("p", class_="parnr")
                
                monitor_info = clean_monitor_text(p_parmo)
                parnr_text = p_parnr.get_text(" ", strip=True) if p_parnr else ""

                numar = extract_number_from_parnr(parnr_text)
                data = extract_date_from_parnr(parnr_text)
                authority = extract_authority_from_parnr(parnr_text)

                if not any([title.strip(), numar.strip(), data.strip(), authority.strip(), monitor_info.strip()]):
                    continue

                key = f"{title}|{numar}|{monitor_info}"
                if key in seen:
                    continue
                seen.add(key)

                rows.append({
                    "title": normalize_romanian_text(title),
                    "numar": numar,
                    "data": normalize_date_format(data),
                    "authority": normalize_romanian_text(authority),
                    "monitor": normalize_romanian_text(monitor_info)
                })

        # Navigare și parsare paginile 2 și 3
        for page_num in (2, 3):
            logger.info("Încerc navigarea la pagina %d...", page_num)
            
            # Mai întâi încercăm click pe link-ul numeric vizibil
            success = False
            try:
                # Identifică elementul de paginare conform imaginii (.page-link)
                page.wait_for_selector('.pagination', timeout=10000)
                
                # Încercăm click direct pe numărul paginii
                selector = f'.pagination .page-link:text("{page_num}")'
                if page.locator(selector).count() > 0:
                    page.click(selector)
                    logger.info(f"Click pe pagina {page_num} prin selector text")
                    success = True
                else:
                    # Alternativă: căutăm a doua/treia pagină
                    page_links = page.locator('.pagination .page-link')
                    count = page_links.count()
                    
                    if count >= page_num:
                        # Link-urile pot fi 'Previous', '1', '2', '3', etc, 'Next'
                        # Pentru pagina 2, ar trebui să fie al treilea element (index 2)
                        # Pentru pagina 3, ar trebui să fie al patrulea element (index 3)
                        page_links.nth(page_num).click()
                        logger.info(f"Click pe pagina {page_num} prin index")
                        success = True
                
                if success:
                    # Așteaptă încărcarea paginii
                    page.wait_for_timeout(2000)
                    page.wait_for_load_state("networkidle", timeout=10000)
                    
                    # Verifică dacă am ajuns pe pagina corectă (căutăm un indicator)
                    active_page = page.locator('.pagination .page-item.active')
                    if active_page.count() > 0:
                        logger.info(f"Navigat cu succes la pagina {page_num} - confirmat")
                    else:
                        logger.warning(f"Navigare posibilă la pagina {page_num}, dar fără confirmare")
            except Exception as e:
                logger.error(f"Eroare la navigare către pagina {page_num}: {e}")
                continue  # încercăm următoarea pagină dacă aceasta eșuează

            # Procesarea conținutului paginii curente
            try:
                page.wait_for_selector('div.table-responsive#dynamic_content', timeout=30000)
                page.wait_for_timeout(1000)
            except Exception:
                logger.warning(f"Selector dynamic_content absent pe pagina {page_num}")

            html = page.content()
            page_htmls.append(html)

            soup = BeautifulSoup(html, "html.parser")
            target_div = soup.select_one("div.table-responsive#dynamic_content") or soup.select_one("div.table-responsive")
            
            if not target_div:
                logger.warning(f"Container absent pe pagina {page_num}")
                continue

            paraar_tags = target_div.find_all("p", class_="paraar")
            page_counts.append(len(paraar_tags))
            primary_total += len(paraar_tags)
            logger.info("Pagina %d: %d inițiative găsite", page_num, len(paraar_tags))

            for p_paraar in paraar_tags:
                parent_div = p_paraar.find_parent("div")
                if not parent_div:
                    continue

                title = p_paraar.get_text(" ", strip=True)
                if not title:
                    continue

                p_parmo = parent_div.find("p", class_="parmo")
                p_parnr = parent_div.find("p", class_="parnr")
                monitor_info = clean_monitor_text(p_parmo)
                parnr_text = p_parnr.get_text(" ", strip=True) if p_parnr else ""

                numar = extract_number_from_parnr(parnr_text)
                data = extract_date_from_parnr(parnr_text)
                authority = extract_authority_from_parnr(parnr_text)

                if not any([title.strip(), numar.strip(), data.strip(), authority.strip(), monitor_info.strip()]):
                    continue

                key = f"{title}|{numar}|{monitor_info}"
                if key in seen:
                    continue
                seen.add(key)

                rows.append({
                    "title": normalize_romanian_text(title),
                    "numar": numar,
                    "data": normalize_date_format(data),
                    "authority": normalize_romanian_text(authority),
                    "monitor": normalize_romanian_text(monitor_info)
                })

    # Închide browser-ul înainte de alte operațiuni
    try:
        browser.close()
        logger.info("Browser-ul a fost închis cu succes")
    except Exception as e:
        logger.warning(f"Eroare la închiderea browser-ului: {e}")

    # --- salvare CSV (atomică) ---
    logger.info("Salvare metadate în CSV...")
    df = pd.DataFrame(rows)
    df = df.drop_duplicates(subset=["title", "numar", "data", "authority", "monitor"])
    _atomic_save_df(df, OUTPUT_CSV)
    logger.info("Salvare finalizată: %d rânduri unice", len(df))

    # --- pentru debug și diagnostic ---
    logger.info("Statistici:")
    for i, count in enumerate(page_counts):
        logger.info("Pagina %d: %d inițiative găsite", i + 1, count)
    logger.info("Total inițiative găsite direct: %d", primary_total)
    logger.info("Total inițiative după deduplicare și filtrare: %d", len(rows))

    # Creează dataframe
    df = pd.DataFrame(rows)

    # Adaugă un URL generator care va fi folosit în a doua etapă
    df['pdf_url'] = ""  # se va completa în etapa a doua
    df['pdf_path'] = ""  # se va completa în etapa a doua
    df['pdf_status'] = "pending"  # se va completa în etapa a doua

    return df

def extract_text_from_pdf(pdf_path: Path) -> str:
    """Extrage text din PDF folosind pdfminer."""
    try:
        from pdfminer.high_level import extract_text
    except ImportError:
        logger.error("pdfminer nu este instalat. Folosește `pip install pdfminer.six` pentru a-l instala.")
        return ""

    try:
        text = extract_text(pdf_path)
        text = re.sub(r"\s+\n", "\n", text)
        return text.strip()
    except Exception as e:
        logger.warning(f"Eroare extragere text din PDF {pdf_path}: {e}")
        return ""

def post_process_stage(df: pd.DataFrame) -> pd.DataFrame:
    """
    Etapa de post-procesare:
    - Extrage text din PDF-urile descărcate
    - Completează sau corectează metadatele din CSV
    """
    # Definim funcția clean_monitor_text local pentru a o avea disponibilă în acest context
    def clean_monitor_text(p_parmo_tag) -> str:
        if not p_parmo_tag:
            return ""
        # Creăm o copie a elementului pentru a nu modifica originalul
        tmp = BeautifulSoup(str(p_parmo_tag), "html.parser")
        # Extragem primul element (care va fi <p class="parmo">)
        p_copy = tmp.find("p")
        if not p_copy:
            return normalize_romanian_text(p_parmo_tag.get_text(" ", strip=True))
        # Eliminăm linkurile
        for a in p_copy.find_all("a"):
            a.extract()
        txt = p_copy.get_text(" ", strip=True)
        return normalize_romanian_text(re.sub(r"\s+", " ", txt).strip())
        
    logger.info("POST-PROCESS STAGE: start")
    updated_rows = []
    pdf_paths = {p.stem: p for p in OUTPUT_DIR.glob("*.pdf")}

    for i, row in tqdm(df.iterrows(), total=len(df), desc="Procesare rânduri"):
        title = row["title"]
        numar = row["numar"]
        data = row["data"]
        authority = row["authority"]
        monitor = row["monitor"]
        pdf_url = row.get("pdf_url")  # presupunând că ai adăugat coloana pdf_url în etapa anterioară

        # Normalizează și reîmpacă datele
        title = normalize_romanian_text(title)
        authority = normalize_romanian_text(authority)

        # Găsește fișierul PDF corespunzător
        pdf_path = None
        if pd.isna(pdf_url) or not pdf_url.strip():
            # Fallback: caută după număr sau titlu
            key = numar or title
            if key:
                key = sanitize_filename(key)
                pdf_path = pdf_paths.get(key)
        else:
            # Încearcă să construiești URL-ul absolut și să ghicești numele fișierului
            try:
                absolute_url = build_absolute_url(START_URL, pdf_url)
                logger.info(f"URL PDF: {absolute_url}")
                pdf_path = download_pdf(absolute_url, OUTPUT_DIR, requests.Session())
            except Exception as e:
                logger.warning(f"Eroare descărcare PDF {pdf_url}: {e}")

        if pdf_path and pdf_path.exists():
            logger.info(f"Fișier PDF găsit: {pdf_path}")
            # Extrage textul din PDF
            pdf_text = extract_text_from_pdf(pdf_path)

            # Salvare metadate extrase înapoi în rând
            if not title:
                title = find_nearest_heading(BeautifulSoup(pdf_text, "html.parser"))
            if not data:
                data = extract_date(pdf_text)
            if not authority:
                authority = extract_authority(pdf_text)
            if not monitor:
                monitor = clean_monitor_text(BeautifulSoup(pdf_text, "html.parser").find("p", class_="parmo"))

            # Normalizează rezultatele
            title = normalize_romanian_text(title)
            data = normalize_date_format(data)
            authority = normalize_romanian_text(authority)
            monitor = normalize_romanian_text(monitor)

            updated_rows.append({
                "title": title,
                "numar": numar,
                "data": data,
                "authority": authority,
                "monitor": monitor,
                "pdf_url": str(pdf_path),  # salvăm calea PDF-ului descărcat
            })
        else:
            logger.warning(f"Fișier PDF inexistent pentru rândul {i+1}: {pdf_path}")
            updated_rows.append(row.to_dict())  # păstrează rândul original în caz de eroare

    # Salvare CSV actualizat
    logger.info("Salvare CSV actualizat...")
    updated_df = pd.DataFrame(updated_rows)
    updated_df = updated_df.drop_duplicates(subset=["title", "numar", "data", "authority", "monitor"])
    _atomic_save_df(updated_df, OUTPUT_CSV)
    logger.info("Salvare finalizată: %d rânduri unice", len(updated_df))

    return updated_df

def run_full_pipeline():
    """
    Rulează întreaga pipeline: scrapează metadatele, descarcă PDF-urile, extrage textul și salvează rezultatele finale.
    """
    # Etapa 1: scrapează metadatele
    df_metadata = scrape_metadata_stage()

    # Etapa 2: extragere și procesare text din PDF-uri
    df_final = post_process_stage(df_metadata)

    logger.info("Pipeline completă. Verifică fișierele CSV și PDF în directoarele corespunzătoare.")

def scrape_pdf_stage(metadata_df: pd.DataFrame) -> pd.DataFrame:
    """
    Descarcă PDF-urile pentru metadatele găsite în prima etapă.
    - Caută URL-urile PDF pe site
    - Descarcă PDF-urile
    - Extrage textul din PDF-uri pentru analiză
    """
    logger.info("PDF STAGE: start")
    
    # Creează directorul pentru PDF-uri
    ensure_dir(OUTPUT_DIR)
    
    # Creăm o sesiune HTTP pentru a reutiliza conexiunile
    session = requests.Session()
    session.headers.update({
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/116.0.0.0 Safari/537.36"
    })
    
    # Limităm la primele MAX_ITEMS elemente pentru a evita prea multe descărcări
    target_items = metadata_df.head(MAX_ITEMS).copy()
    
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(locale="ro-RO")
        page = context.new_page()
        page.set_default_timeout(TIMEOUT_MS)
        
        for idx, row in tqdm(target_items.iterrows(), total=len(target_items), desc="Descărcare PDF-uri"):
            title = row["title"]
            try:
                # Construiește un URL de căutare bazat pe titlu sau număr
                search_term = row["numar"] if row["numar"] else title[:50]
                search_url = f"https://monitoruloficial.ro/acte-publicate-in-monitorul-oficial-partea-i/?s={search_term}"
                
                logger.info(f"Căutare PDF pentru: {title[:50]}...")
                page.goto(search_url, wait_until="networkidle", timeout=60000)
                
                # Așteaptă ca rezultatele să se încarce
                page.wait_for_timeout(2000)
                
                # Caută link-uri către PDF-uri 
                pdf_links = page.locator('a[href*=".pdf"]').all()
                
                if pdf_links:
                    # Ia primul link PDF găsit
                    pdf_url = pdf_links[0].get_attribute("href")
                    logger.info(f"PDF găsit: {pdf_url}")
                    
                    try:
                        pdf_path = download_pdf(pdf_url, OUTPUT_DIR, session)
                        metadata_df.at[idx, "pdf_url"] = pdf_url
                        metadata_df.at[idx, "pdf_path"] = str(pdf_path)
                        metadata_df.at[idx, "pdf_status"] = "downloaded"
                        
                        # Opțional: extrage text din PDF pentru analiză
                        # pdf_text = extract_pdf_text(pdf_path)
                        # metadata_df.at[idx, "pdf_text"] = pdf_text[:1000]  # primele 1000 caractere pentru preview
                        
                        # Salvare incrementală pentru a nu pierde progresul
                        if idx % 5 == 0:
                            _atomic_save_df(metadata_df, OUTPUT_CSV)
                    except Exception as e:
                        logger.error(f"Eroare la descărcarea PDF-ului: {e}")
                        metadata_df.at[idx, "pdf_status"] = f"error: {str(e)[:100]}"
                else:
                    logger.warning(f"Nu s-a găsit PDF pentru: {title[:50]}")
                    metadata_df.at[idx, "pdf_status"] = "not_found"
            except Exception as e:
                logger.error(f"Eroare la procesarea elementului {idx}: {e}")
                metadata_df.at[idx, "pdf_status"] = f"error: {str(e)[:100]}"
            
            # Pauză între descărcări pentru a evita supraîncărcarea serverului
            time.sleep(1)
        
        # Închide browser-ul
        try:
            browser.close()
            logger.info("Browser-ul a fost închis cu succes")
        except Exception as e:
            logger.warning(f"Eroare la închiderea browser-ului: {e}")
    
    # Salvează rezultatele finale
    _atomic_save_df(metadata_df, OUTPUT_CSV)
    logger.info(f"Datele au fost salvate în {OUTPUT_CSV}")
    
    return metadata_df

def main():
    """
    Funcția principală care coordonează fluxul de scraping
    """
    try:
        logger.info("Inițializare scraper...")
        
        # Etapa 1: Extrage metadatele
        metadata_df = scrape_metadata_stage()
        logger.info(f"S-au extras metadate pentru {len(metadata_df)} documente")
        
        # Salvează intermediar doar metadatele
        _atomic_save_df(metadata_df, OUTPUT_CSV)
        logger.info(f"Metadatele au fost salvate în {OUTPUT_CSV}")
        
        # Etapa 2: Descarcă PDF-urile
        if len(metadata_df) > 0:
            logger.info("Începe descărcarea PDF-urilor...")
            final_df = scrape_pdf_stage(metadata_df)
            
            # Statistici finale
            downloaded = sum(final_df["pdf_status"] == "downloaded")
            errors = sum(final_df["pdf_status"].str.startswith("error"))
            not_found = sum(final_df["pdf_status"] == "not_found")
            
            logger.info(f"Statistici finale:")
            logger.info(f"- Total documente procesate: {len(final_df)}")
            logger.info(f"- PDF-uri descărcate cu succes: {downloaded}")
            logger.info(f"- PDF-uri negăsite: {not_found}")
            logger.info(f"- Erori: {errors}")
        else:
            logger.warning("Nu s-au găsit metadate pentru procesare")
        
        logger.info("Procesare completă!")
        
    except Exception as e:
        logger.exception(f"Eroare globală: {e}")
        raise

if __name__ == "__main__":
    main()
