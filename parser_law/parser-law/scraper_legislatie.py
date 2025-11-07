#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Script principal pentru parsarea automată a actelor legislative
Citește linkuri din fișier și salvează rezultatele în format Excel
"""

import os
import re
import time
import requests
from urllib.parse import urlparse
from datetime import datetime
from typing import List, Optional
import pandas as pd
from bs4 import BeautifulSoup

from hybrid_parser import HybridLegislativeParser

class LegislationScraper:
    def __init__(self, links_file: str = "linkuri_legislatie.txt", output_dir: str = "rezultate"):
        """
        Inițializează scraper-ul pentru legislație
        
        Args:
            links_file: Calea către fișierul cu linkuri
            output_dir: Directorul unde se salvează rezultatele
        """
        self.links_file = links_file
        self.output_dir = output_dir
        self.session = requests.Session()
        
        # Headers pentru a simula un browser real
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'ro-RO,ro;q=0.9,en;q=0.8',
            'Accept-Encoding': 'gzip, deflate, br',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
        })
        
        # Crează directorul de output dacă nu există
        os.makedirs(self.output_dir, exist_ok=True)
    
    def read_links(self) -> List[str]:
        """
        Citește linkurile din fișier, ignorând comentariile și liniile goale
        
        Returns:
            Lista de linkuri URL
        """
        links = []
        
        if not os.path.exists(self.links_file):
            print(f"❌ Fișierul {self.links_file} nu există!")
            return links
        
        with open(self.links_file, 'r', encoding='utf-8') as f:
            for line_num, line in enumerate(f, 1):
                line = line.strip()
                
                # Ignoră liniile goale și comentariile
                if not line or line.startswith('#'):
                    continue
                
                # Validează că este un URL valid
                if self.is_valid_url(line):
                    links.append(line)
                else:
                    print(f"⚠️  Linia {line_num}: URL invalid ignorat: {line}")
        
        print(f"📋 Am găsit {len(links)} linkuri valide în {self.links_file}")
        return links
    
    def is_valid_url(self, url: str) -> bool:
        """
        Verifică dacă URL-ul este valid și de la legislatie.just.ro
        
        Args:
            url: URL-ul de verificat
            
        Returns:
            True dacă URL-ul este valid
        """
        try:
            result = urlparse(url)
            return (result.scheme in ['http', 'https'] and 
                   'legislatie.just.ro' in result.netloc)
        except Exception:
            return False
    
    def get_printable_url(self, base_url: str) -> str:
        """
        Convertește URL-ul de bază în URL pentru forma printabilă
        
        Args:
            base_url: URL-ul original
            
        Returns:
            URL-ul pentru forma printabilă
        """
        # Dacă deja conține 'FormaConsolidata', returnează cum este
        if 'FormaConsolidata' in base_url:
            return base_url
        
        # Altfel, încearcă să construiască URL-ul pentru forma printabilă
        if 'DetaliiDocument' in base_url:
            # Extrage ID-ul documentului
            match = re.search(r'DetaliiDocument/(\d+)', base_url)
            if match:
                doc_id = match.group(1)
                return f"https://legislatie.just.ro/Public/FormaConsolidata/{doc_id}"
        
        return base_url
    
    def download_document(self, url: str) -> Optional[str]:
        """
        Descarcă conținutul documentului de la URL
        
        Args:
            url: URL-ul documentului
            
        Returns:
            Conținutul textual al documentului sau None dacă a eșuat
        """
        try:
            print(f"📥 Descarc: {url}")
            
            # Încearcă mai multe strategii, prioritizând FormaPrintabila (versiune curată)
            urls_to_try = []
            
            # Detectează și convertește URL-ul către FormaPrintabila
            if 'FormaPrintabila' in url:
                # Deja e FormaPrintabila, folosește direct
                urls_to_try.append(url)
            elif 'DetaliiDocument' in url or 'FormaConsolidata' in url:
                # Extrage ID-ul (poate fi numeric sau alfanumeric)
                match = re.search(r'(?:DetaliiDocument|FormaConsolidata)/([A-Z0-9]+)', url)
                if match:
                    doc_id = match.group(1)
                    # PRIORITATE: FormaPrintabila (fără linkuri către alte acte)
                    urls_to_try.extend([
                        f"https://legislatie.just.ro/Public/FormaPrintabila/{doc_id}",
                        f"https://legislatie.just.ro/Public/FormaConsolidata/{doc_id}",
                        url  # URL-ul original ca fallback
                    ])
                else:
                    urls_to_try.append(url)
            else:
                urls_to_try.append(url)
            
            last_error = None
            for attempt_url in urls_to_try:
                try:
                    if attempt_url != url:
                        print(f"   → Încerc: {attempt_url}")
                    
                    # Configurează sesiunea pentru această cerere
                    response = self.session.get(
                        attempt_url, 
                        timeout=30, 
                        allow_redirects=True
                    )
                    response.raise_for_status()
                    
                    # Verifică dacă am primit conținut util
                    if len(response.text) < 100:
                        print(f"   ⚠️  Răspuns prea scurt ({len(response.text)} caractere)")
                        continue
                    
                    # Încearcă să detecteze encoding-ul
                    if response.encoding is None:
                        response.encoding = 'utf-8'
                    
                    print(f"   ✅ Succes cu {attempt_url}")
                    print(f"   📄 Dimensiune conținut: {len(response.text)} caractere")
                    
                    return response.text
                    
                except requests.exceptions.TooManyRedirects:
                    last_error = f"Prea multe redirecturi pentru {attempt_url}"
                    print(f"   ❌ {last_error}")
                    continue
                except requests.exceptions.RequestException as e:
                    last_error = f"Eroare cerere pentru {attempt_url}: {e}"
                    print(f"   ❌ {last_error}")
                    continue
            
            print(f"❌ Toate încercările au eșuat. Ultima eroare: {last_error}")
            return None
            
        except Exception as e:
            print(f"❌ Eroare neașteptată pentru {url}: {e}")
            return None
    
    def extract_text_from_html(self, html_content: str) -> Optional[str]:
        """
        Extrage textul curat din conținutul HTML
        
        Args:
            html_content: Conținutul HTML
            
        Returns:
            Textul curat sau None dacă nu se poate extrage
        """
        try:
            soup = BeautifulSoup(html_content, 'html.parser')
            
            # Încearcă să găsească containerul principal cu conținutul
            # Caută diverse clase/id-uri comune pentru conținutul legislativ
            content_selectors = [
                '#content',
                '.content',
                '#main-content',
                '.main-content',
                '.document-content',
                '.law-content',
                '.act-content',
                'main',
                '.container',
                'body'
            ]
            
            text_content = None
            for selector in content_selectors:
                element = soup.select_one(selector)
                if element:
                    # Elimină scripturile și stilurile
                    for script in element(["script", "style", "nav", "header", "footer"]):
                        script.decompose()
                    
                    text_content = element.get_text(separator='\n', strip=True)
                    if len(text_content) > 1000:  # Să fie suficient de substanțial
                        break
            
            if not text_content:
                # Fallback: extrage tot textul din body
                text_content = soup.get_text(separator='\n', strip=True)
            
            if text_content and len(text_content) > 500:
                return text_content
            
            return None
            
        except Exception as e:
            print(f"⚠️  Eroare la extragerea textului din HTML: {e}")
            return None
    
    def extract_document_id(self, url: str) -> str:
        """
        Extrage ID-ul documentului din URL pentru nume fișier
        
        Args:
            url: URL-ul documentului
            
        Returns:
            ID-ul documentului sau timestamp dacă nu poate fi extras
        """
        match = re.search(r'(?:DetaliiDocument|FormaConsolidata)/(\d+)', url)
        if match:
            return match.group(1)
        
        # Fallback: folosește timestamp
        return datetime.now().strftime("%Y%m%d_%H%M%S")
    
    def process_document(self, url: str, index: int, total: int) -> bool:
        """
        Procesează un singur document: descarcă, parsează și salvează
        
        Args:
            url: URL-ul documentului
            index: Indexul curent (pentru progres)
            total: Numărul total de documente
            
        Returns:
            True dacă procesarea a avut succes
        """
        print(f"\n🔄 Procesez documentul {index}/{total}")
        
        # Descarcă conținutul
        content = self.download_document(url)
        if not content:
            return False
        
        try:
            # Folosește parserul hibrid nou (simplificat și robust)
            print("⚙️  Parsez conținutul...")
            parser = HybridLegislativeParser()
            df, metrics = parser.parse(content, content_type='html')
            
            if df.empty:
                print("⚠️  Nu am găsit date parsabile în document")
                
                # Salvează conținutul pentru debugging
                doc_id = self.extract_document_id(url)
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                debug_file = os.path.join(self.output_dir, f"debug_content_{timestamp}.txt")
                with open(debug_file, 'w', encoding='utf-8') as f:
                    f.write(content)
                print(f"🐛 Conținut complet salvat în: debug_content_{timestamp}.txt")
                return False
            
            # Generează numele fișierului
            doc_id = self.extract_document_id(url)
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            
            # Salvează folosind metoda din hybrid_parser (CSV + Markdown)
            saved_files = parser.save_to_rezultate(df, f"act_legislativ_{doc_id}", metrics)
            
            if saved_files.get('csv'):
                csv_filename = os.path.basename(saved_files['csv'])
                print(f"✅ Salvat CSV: {csv_filename}")
            if saved_files.get('markdown'):
                md_filename = os.path.basename(saved_files['markdown'])
                print(f"✅ Salvat MD:  {md_filename}")
            print(f"   📊 {len(df)} articole procesate")
            print(f"   🎯 Confidence: {metrics['confidence']:.2f}")
            
            # Afișează informații sumare
            if not df.empty and 'tip_act' in df.columns:
                first_row = df.iloc[0]
                if first_row.get('tip_act'):
                    nr = first_row.get('nr_act', '')
                    data = first_row.get('data_an', '')
                    print(f"   📄 {first_row['tip_act']} nr. {nr}/{data}")
                if first_row.get('titlu_act'):
                    print(f"   📝 {first_row['titlu_act'][:80]}...")
            
            return True
            
        except Exception as e:
            print(f"❌ Eroare la procesarea documentului: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    def run(self, delay_seconds: float = 2.0) -> None:
        """
        Rulează procesarea pentru toate linkurile din fișier
        
        Args:
            delay_seconds: Paiza între cereri (pentru a fi respectuoși cu serverul)
        """
        print("🚀 Încep procesarea actelor legislative...")
        print(f"📁 Rezultatele vor fi salvate în: {os.path.abspath(self.output_dir)}")
        print("=" * 70)
        
        # Citește linkurile
        links = self.read_links()
        if not links:
            print("❌ Nu am găsit linkuri valide pentru procesare!")
            return
        
        # Procesează fiecare link
        successful = 0
        failed = 0
        
        for i, url in enumerate(links, 1):
            success = self.process_document(url, i, len(links))
            
            if success:
                successful += 1
            else:
                failed += 1
            
            # Pauză între cereri (doar dacă nu este ultimul)
            if i < len(links):
                print(f"⏳ Pauză {delay_seconds} secunde...")
                time.sleep(delay_seconds)
        
        # Afișează rezultatele finale
        print("\n" + "=" * 70)
        print("🏁 Procesare finalizată!")
        print(f"✅ Succes: {successful} documente")
        print(f"❌ Eșec: {failed} documente")
        print(f"📁 Fișierele sunt salvate în: {os.path.abspath(self.output_dir)}")


def main():
    """Funcția principală"""
    print("🏛️  Scraper pentru Acte Legislative")
    print("=" * 50)
    
    # Inițializează scraper-ul
    scraper = LegislationScraper()
    
    # Rulează procesarea
    scraper.run(delay_seconds=2.0)


if __name__ == "__main__":
    main()