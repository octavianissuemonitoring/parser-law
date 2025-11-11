#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Parser simplificat pentru actele legislative - folosește doar strategia HTML CSS care funcționează perfect
Cod redus cu ~60% față de versiunea anterioară, menținând 100% funcționalitatea
"""

import re
import pandas as pd
from typing import Dict, List, Optional, Any, Tuple
from bs4 import BeautifulSoup
import logging
import os
import json
from datetime import datetime

from src.scraper.html_parser import parse_html_legislative_structure

# Configurare logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def int_to_roman(num: int) -> str:
    """Convertește un număr întreg în cifre romane"""
    if pd.isna(num) or num == 0:
        return ''
    
    num = int(num)
    val = [
        1000, 900, 500, 400,
        100, 90, 50, 40,
        10, 9, 5, 4,
        1
    ]
    syms = [
        'M', 'CM', 'D', 'CD',
        'C', 'XC', 'L', 'XL',
        'X', 'IX', 'V', 'IV',
        'I'
    ]
    roman_num = ''
    i = 0
    while num > 0:
        for _ in range(num // val[i]):
            roman_num += syms[i]
            num -= val[i]
        i += 1
    return roman_num

class HybridLegislativeParser:
    """
    Parser simplificat care folosește doar strategia HTML CSS (optimă pentru 95% din documente)
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """Inițializează parserul cu configurație"""
        self.config = config or {}
        self.debug_mode = self.config.get('debug', False)
        self.last_html_content = None  # Salvează ultimul HTML parsat pentru generare Markdown
        self.last_soup = None  # Salvează BeautifulSoup object
        self.last_metadata = None  # Salvează metadata extrasă
    
    def parse(self, content: str, content_type: str = 'auto') -> Tuple[pd.DataFrame, Dict[str, Any]]:
        """
        Parsează conținutul folosind strategia HTML CSS
        
        Args:
            content: Conținutul de parsat (HTML)
            content_type: 'html' sau 'auto' pentru detectare automată
            
        Returns:
            Tuple cu (DataFrame cu rezultate, metrici de parsare)
        """
        
        # Detectează tipul conținutului dacă e setat pe auto
        if content_type == 'auto':
            content_type = self._detect_content_type(content)
        
        logger.info(f"🚀 Încep parsarea pentru conținut de tip: {content_type}")
        
        metrics = {
            'content_type': content_type,
            'strategy_used': 'html_css_specific',
            'confidence': 0.0,
            'total_elements': 0,
            'parsing_errors': []
        }
        
        if content_type != 'html':
            logger.warning("⚠️ Conținutul nu este HTML")
            return pd.DataFrame(), metrics
        
        try:
            # Parsare HTML cu CSS
            df = parse_html_legislative_structure(content)
            
            if df.empty:
                logger.warning("⚠️ Nu s-au găsit date parsabile în document")
                return pd.DataFrame(), metrics
            
            # Extrage metadata și o adaugă la toate rândurile
            soup = BeautifulSoup(content, 'html.parser')
            metadata = self._extract_html_metadata(soup)
            
            # Salvează pentru generare Markdown
            self.last_html_content = content
            self.last_soup = soup
            self.last_metadata = metadata
            
            # Mapare lowercase -> uppercase (pentru verificare)
            col_uppercase_map = {
                'tip_act': 'Tip_Act',
                'nr_act': 'Nr',
                'data_act': 'Data_An',
                'titlu_act': 'Denumire',
                'mof_nr': 'Mof_nr',
                'mof_data': 'Mof_Data'
            }
            
            # Adaugă metadata DOAR dacă nu există deja în nicio variantă (lowercase sau uppercase)
            for col, value in metadata.items():
                uppercase_col = col_uppercase_map.get(col, col)
                
                # Verifică dacă există în uppercase SAU lowercase
                has_uppercase = uppercase_col in df.columns and not df[uppercase_col].isna().all()
                has_lowercase = col in df.columns and not df[col].isna().all()
                
                # Adaugă DOAR dacă nu există în NICIO variantă
                if not has_uppercase and not has_lowercase:
                    if col not in df.columns:
                        df[col] = value
            
            df = self._post_process_results(df)
            
            # Validare structurală post-extracție
            validation_results = self._validate_extraction(df)
            
            # Calculează confidence
            confidence = df['confidence_score'].iloc[0] if 'confidence_score' in df.columns else 0.0
            
            metrics['confidence'] = confidence
            metrics['total_elements'] = len(df)
            metrics['validation'] = validation_results
            
            logger.info(f"🎯 Parsare finalizată:")
            logger.info(f"   • Confidence: {confidence:.2f}")
            logger.info(f"   • Elemente extrase: {len(df)}")
            if not validation_results['is_valid']:
                logger.warning(f"   ⚠️  Validare: {len(validation_results['issues'])} issues detectate")
            
            return df, metrics
                
        except Exception as e:
            error_msg = f"Eroare la parsare: {str(e)}"
            logger.error(error_msg)
            metrics['parsing_errors'].append(error_msg)
            return pd.DataFrame(), metrics
    
    def _detect_content_type(self, content: str) -> str:
        """Detectează tipul conținutului"""
        content_lower = content.lower().strip()
        
        if content_lower.startswith('<!doctype') or content_lower.startswith('<html'):
            return 'html'
        elif '<div' in content_lower and 'class=' in content_lower:
            return 'html'
        else:
            return 'text'
    
    def _extract_html_metadata(self, soup: BeautifulSoup) -> Dict[str, Any]:
        """
        Extrage metadata completă din HTML (tip_act, nr_act, data_act, titlu_act, emitent_act, MOF).
        Această metodă extrage TOATĂ metadata necesară pentru generare Markdown.
        """
        metadata: Dict[str, Any] = {
            'tip_act': None,
            'nr_act': None,
            'data_act': None,
            'titlu_act': None,
            'emitent_act': None,
            'mof_nr': None,
            'mof_data': None
        }
        
        # Extrage din S_DEN (cel mai precis)
        s_den = soup.find(class_='S_DEN')
        if s_den:
            den_text = s_den.get_text(strip=True)
            
            # Pattern-uri pentru diferite formate
            patterns = [
                r'(LEGE|ORDONANȚ[AĂ]\s+DE\s+URGEN[TȚ][AĂ]|ORDONANȚ[AĂ]|HOT[AĂ]R[ÂÎ]RE|DECRET|ORDIN|REGULAMENT|NORM[AĂ]|INSTRUC[TȚ]IUNE|METODOLOGIE)\s+nr\.?\s*(\d+)\s+din\s+(\d{1,2})\s+(\w+)\s+(\d{4})',
                r'(LEGE|ORDONANȚ[AĂ]\s+DE\s+URGEN[TȚ][AĂ]|ORDONANȚ[AĂ]|HOT[AĂ]R[ÂÎ]RE|DECRET|ORDIN|REGULAMENT|NORM[AĂ]|INSTRUC[TȚ]IUNE|METODOLOGIE)\s+nr\.?\s*(\d+)/(\d{4})',
                r'(METODOLOGIE|REGULAMENT|NORM[AĂ]|INSTRUC[TȚ]IUNE)\s+din\s+(\d{1,2})\s+(\w+)\s+(\d{4})'
            ]
            
            for pattern_idx, pattern in enumerate(patterns):
                match = re.search(pattern, den_text, re.IGNORECASE)
                if match:
                    tip_act = match.group(1).upper()
                    
                    # Normalizează tipul actului
                    if 'URGENȚĂ' in tip_act or 'URGENTA' in tip_act:
                        tip_act = 'ORDONANȚĂ DE URGENȚĂ'
                    elif 'ORDONANȚ' in tip_act:
                        tip_act = 'ORDONANȚĂ'
                    elif 'HOTĂR' in tip_act:
                        tip_act = 'HOTĂRÂRE'
                    elif 'INSTRUCȚ' in tip_act:
                        tip_act = 'INSTRUCȚIUNE'
                    elif 'NORMĂ' in tip_act or 'NORMA' in tip_act:
                        tip_act = 'NORMĂ'
                    elif 'METODOLOGI' in tip_act:
                        tip_act = 'METODOLOGIE'
                    
                    metadata['tip_act'] = tip_act
                    
                    # Pattern 3 (fără număr: "METODOLOGIE din 29 iulie 2025")
                    if pattern_idx == 2:
                        metadata['nr_act'] = None
                        zi = match.group(2)
                        luna = match.group(3)
                        an = match.group(4)
                        luna_nr = self._convert_month_to_number(luna)
                        metadata['data_act'] = f"{zi.zfill(2)}/{luna_nr}/{an}"
                    else:
                        # Pattern 1 și 2 (cu număr)
                        metadata['nr_act'] = int(match.group(2))
                        
                        if pattern_idx == 0:
                            # Pattern 1: "LEGE nr. 123 din 30 aprilie 2024"
                            zi = match.group(3)
                            luna = match.group(4)
                            an = match.group(5)
                            luna_nr = self._convert_month_to_number(luna)
                            metadata['data_act'] = f"{zi.zfill(2)}/{luna_nr}/{an}"
                        else:
                            # Pattern 2: "LEGE nr. 123/2024"
                            an = match.group(3)
                            metadata['data_act'] = f"01/01/{an}"  # Dată aproximativă
                    
                    break
        
        # Extrage denumirea din S_HDR
        s_hdr = soup.find('span', class_='S_HDR')
        if s_hdr:
            metadata['titlu_act'] = s_hdr.get_text(strip=True)
        
        # Extrage emitentul din S_EMT_BDY
        s_emt_bdy = soup.find('span', class_='S_EMT_BDY')
        if s_emt_bdy:
            metadata['emitent_act'] = s_emt_bdy.get_text(strip=True)
        
        # Extrage info MOF din S_PUB_BDY
        s_pub_bdy = soup.find('span', class_='S_PUB_BDY')
        if s_pub_bdy:
            text = s_pub_bdy.get_text(strip=True)
            
            # Extrage numărul Monitorului Oficial
            match_mof_nr = re.search(r'nr\.?\s*(\d+)', text, re.I)
            if match_mof_nr:
                metadata['mof_nr'] = int(match_mof_nr.group(1))
            
            # Extrage data publicării în MOF
            match_mof_data = re.search(r'din\s+(\d+)\s+(\w+)\s+(\d{4})', text, re.I)
            if match_mof_data:
                zi, luna, an = match_mof_data.groups()
                luna_nr = self._convert_month_to_number(luna)
                metadata['mof_data'] = f"{zi.zfill(2)}/{luna_nr}/{an}"
        
        return metadata
    
    def _convert_month_to_number(self, luna: str) -> str:
        """Convertește luna din text în număr (01-12)"""
        luni_map = {
            'ianuarie': '01', 'februarie': '02', 'martie': '03', 'aprilie': '04',
            'mai': '05', 'iunie': '06', 'iulie': '07', 'august': '08',
            'septembrie': '09', 'octombrie': '10', 'noiembrie': '11', 'decembrie': '12'
        }
        return luni_map.get(luna.lower(), luna)
    
    def _validate_extraction(self, df: pd.DataFrame) -> Dict[str, Any]:
        """
        Validează calitatea extracției și detectează probleme potențiale.
        
        Returns:
            Dict cu is_valid, issues (listă), quality_score (0-1)
        """
        issues = []
        
        if df.empty:
            return {
                'is_valid': False,
                'issues': ['DataFrame gol - nicio extracție'],
                'quality_score': 0.0
            }
        
        # Verifică duplicates la art_nr
        if 'art_nr' in df.columns:
            duplicates = df[df['art_nr'].duplicated(keep=False)]['art_nr'].dropna().unique()
            if len(duplicates) > 0:
                issues.append(f"Articole duplicate: {list(duplicates)}")
        
        # Verifică secvență articole (lipsă numere)
        if 'art_nr' in df.columns:
            art_numbers = sorted(df['art_nr'].dropna().unique())
            if len(art_numbers) > 1:
                expected = list(range(int(art_numbers[0]), int(art_numbers[-1]) + 1))
                missing = [n for n in expected if n not in art_numbers]
                if missing:
                    issues.append(f"Articole lipsă din secvență: {missing}")
        
        # Verifică articole cu text prea scurt (< 10 caractere)
        if 'text_articol' in df.columns and 'art_nr' in df.columns:
            short_texts = df[df['text_articol'].str.len() < 10]
            if not short_texts.empty:
                short_arts = short_texts['art_nr'].tolist()
                issues.append(f"Articole cu text prea scurt: {short_arts}")
        
        # Calculează quality score
        quality_score = 1.0 - (len(issues) * 0.15)  # -0.15 pentru fiecare issue
        quality_score = max(0.0, quality_score)  # Nu poate fi negativ
        
        return {
            'is_valid': len(issues) == 0,
            'issues': issues,
            'quality_score': round(quality_score, 2)
        }
    
    def _post_process_results(self, df: pd.DataFrame) -> pd.DataFrame:
        """Post-procesează rezultatele pentru consistență"""
        if df.empty:
            return df
        
        # Mapare coloane vechi (UpperCase/MixedCase) -> coloane noi (lowercase_underscore)
        old_to_new = {
            'Tip_Act': 'tip_act',
            'Nr': 'nr_act', 
            'Data_An': 'data_act',
            'Denumire': 'titlu_act',
            'Mof_nr': 'mof_nr',
            'Mof_Data': 'mof_data',
            'Mof_An': 'mof_an',
            'Emitent': 'emitent_act',
            'Titlu_Nr': 'titlu_nr',
            'Titlu_Denumire': 'titlu_denumire',
            'Capitol_Nr': 'capitol_nr',
            'Capitol_Denumire': 'capitol_denumire',
            'Sectiune_Nr': 'sectiune_nr',
            'Sectiune_Denumire': 'sectiune_denumire',
            'Subsectiune_Nr': 'subsectiune_nr',
            'Subsectiune_Denumire': 'subsectiune_denumire',
            'Art.1': 'art_nr',
            'Art.2': 'art_idx',
            'Articol_Label': 'articol_label',
            'Text_Articol': 'text_articol'
        }
        
        # Redenumește coloanele vechi în cele noi
        rename_map = {}
        for old_col, new_col in old_to_new.items():
            if old_col in df.columns:
                # Dacă există ambele, vom șterge pe cea veche mai jos
                # Dacă există doar cea veche, o redenumim
                if new_col not in df.columns:
                    rename_map[old_col] = new_col
        
        if rename_map:
            df = df.rename(columns=rename_map)
        
        # Elimină coloanele duplicate (doar cele vechi dacă există ambele)
        columns_to_remove = []
        for old_col, new_col in old_to_new.items():
            if old_col in df.columns and new_col in df.columns:
                columns_to_remove.append(old_col)
        
        # Elimină coloana art_idx (fost Art.2) - nu își are rostul
        if 'art_idx' in df.columns:
            columns_to_remove.append('art_idx')
        if 'Art.2' in df.columns:
            columns_to_remove.append('Art.2')
        
        if columns_to_remove:
            df = df.drop(columns=columns_to_remove)
        
        # Funcție helper pentru extragere an cu validare
        def extract_year(date_str):
            """Extrage anul din dată (formate: DD/MM/YYYY, DD/luna/YYYY, YYYY)"""
            if pd.isna(date_str) or not date_str:
                return None
            
            try:
                date_str = str(date_str).strip()
                # Caută pattern de 4 cifre pentru an
                match = re.search(r'\b(\d{4})\b', date_str)
                if match:
                    year = int(match.group(1))
                    # Validare: anii între 1900-2100 (legislație românească modernă)
                    if 1900 <= year <= 2100:
                        return year
                    else:
                        logging.warning(f"An invalid detectat: {year} din '{date_str}'")
                        return None
                return None
            except (ValueError, AttributeError) as e:
                logging.warning(f"Eroare la extragerea anului din '{date_str}': {e}")
                return None
        
        # Extrage an_act din data_act
        if 'data_act' in df.columns:
            df['an_act'] = df['data_act'].apply(extract_year)
        
        # Extrage mof_an din mof_data
        if 'mof_data' in df.columns:
            df['mof_an'] = df['mof_data'].apply(extract_year)
        
        # Curățăm articol_label - păstrăm doar "Articolul X"
        if 'articol_label' in df.columns:
            def extract_article_label(text):
                match = re.match(r'(Articolul\s+\d+)', str(text))
                return match.group(1) if match else str(text)
            
            df['articol_label'] = df['articol_label'].apply(extract_article_label)
        
        # Sortează după numărul articolului
        if 'art_nr' in df.columns:
            df['art_nr'] = pd.to_numeric(df['art_nr'], errors='coerce').fillna(0).astype(int)
            df = df.sort_values('art_nr').reset_index(drop=True)
        
        # FIX: Eliminăm rândurile cu text_articol GOL (articole fără conținut - probabil issue markers)
        # Acestea apar când parser-ul confundă numere de issue cu numere de articole
        if 'text_articol' in df.columns and 'articol_label' in df.columns:
            initial_count = len(df)
            # Păstrăm doar rândurile cu conținut real (> 5 caractere după strip)
            df = df[df['text_articol'].astype(str).str.strip().str.len() > 5].copy()
            removed_count = initial_count - len(df)
            if removed_count > 0:
                logger.info(f"🧹 Eliminat {removed_count} rânduri goale (fără conținut text_articol)")
            df = df.reset_index(drop=True)
        
        # Eliminăm duplicatele - păstrăm intrarea cu cel mai mult conținut în text_articol
        if 'art_nr' in df.columns and 'text_articol' in df.columns:
            initial_count = len(df)
            df['_text_length'] = df['text_articol'].astype(str).str.len()
            df = df.sort_values(['art_nr', '_text_length'], ascending=[True, False])
            df = df.drop_duplicates(subset=['art_nr'], keep='first')
            df = df.drop(columns=['_text_length'])
            removed_count = initial_count - len(df)
            if removed_count > 0:
                logger.info(f"🧹 Eliminat {removed_count} duplicate (același art_nr)")
            df = df.reset_index(drop=True)
        
        # Curățăm text_articol - eliminăm label-ul din text dacă există
        if 'text_articol' in df.columns and 'articol_label' in df.columns:
            def clean_text(row):
                text = str(row['text_articol'])
                label = str(row['articol_label'])
                if text.startswith(label):
                    text = text[len(label):].strip()
                return text
            
            df['text_articol'] = df.apply(clean_text, axis=1)
        
        # Curăță textul final
        if 'text_articol' in df.columns:
            df['text_articol'] = df['text_articol'].astype(str).str.strip()
        
        # Adaugă coloane pentru Issue și Explicație (vor fi completate manual)
        if 'issue' not in df.columns:
            df['issue'] = ''
        if 'explicatie' not in df.columns:
            df['explicatie'] = ''
        
        # Convertește numerele în romane pentru titlu_nr, capitol_nr, sectiune_nr
        for col in ['titlu_nr', 'capitol_nr', 'sectiune_nr', 'subsectiune_nr']:
            if col in df.columns:
                df[col] = df[col].apply(lambda x: int_to_roman(x) if pd.notna(x) and x != 0 else '')
        
        # Reordonează coloanele: metadata la început, apoi restul
        metadata_cols = ['tip_act', 'nr_act', 'data_act', 'an_act', 'titlu_act', 'emitent_act', 'mof_nr', 'mof_data', 'mof_an']
        first_cols = [col for col in metadata_cols if col in df.columns]
        
        # Coloane structurale
        structural_cols = ['titlu_nr', 'titlu_denumire', 'capitol_nr', 'capitol_denumire', 
                          'sectiune_nr', 'sectiune_denumire', 'subsectiune_nr', 'subsectiune_denumire']
        middle_cols = [col for col in structural_cols if col in df.columns]
        
        # Coloane de articol
        article_cols = ['art_nr', 'articol_label', 'text_articol', 'issue', 'explicatie']
        last_cols = [col for col in article_cols if col in df.columns]
        
        # Restul coloanelor
        other_cols = [col for col in df.columns 
                     if col not in first_cols + middle_cols + last_cols]
        
        # Reordonează
        df = df[first_cols + middle_cols + last_cols + other_cols]
        
        return df
    
    def _generate_statistics(self, df: pd.DataFrame, validation: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Generează statistici despre rezultatele parsării"""
        stats = {
            'total_articole': len(df),
            'articole_cu_continut': len(df[df['text_articol'].str.len() > 10]) if 'text_articol' in df.columns else 0,
            'total_caractere': int(df['text_articol'].str.len().sum()) if 'text_articol' in df.columns else 0,
            'lungime_medie': float(df['text_articol'].str.len().mean()) if 'text_articol' in df.columns else 0.0,
            'capitole_identificate': int(df['capitol_nr'].nunique()) if 'capitol_nr' in df.columns else 0,
            'sectiuni_identificate': int(df['sectiune_nr'].nunique()) if 'sectiune_nr' in df.columns else 0
        }
        
        # Adaugă validation dacă există
        if validation:
            stats['validation'] = validation
        
        return stats
    
    def _format_article_text(self, text: str) -> str:
        """
        Formatează textul articolului pentru lizibilitate în Markdown
        - Pune fiecare alineat (1), (2), etc. pe rând nou
        - Pune fiecare literă a), b), c) pe rând nou și indentată
        
        Args:
            text: Textul brut al articolului
            
        Returns:
            Text formatat cu alineate și litere pe rânduri separate
        """
        if not text:
            return text
        
        # Verifică dacă începe cu alineat (1), (2), etc.
        if not re.match(r'^\(\d+\)\s+[A-ZĂÎÂȘȚ]', text):
            # Nu începe cu alineat - verifică dacă are litere cu separator ";..."
            if ';...' in text:
                return self._format_litere(text)
            return text.strip()
        
        # Are alineate - split pe pattern care prinde doar alineate urmate de majusculă
        # Regex: (cifră) urmat de spațiu și majusculă (începutul unei propoziții)
        parts = re.split(r'\((\d+)\)\s+(?=[A-ZĂÎÂȘȚ])', text)
        
        formatted_lines = []
        
        # Prima parte (înainte de primul alineat) - de obicei goală
        if parts[0].strip():
            formatted_lines.append(parts[0].strip())
            formatted_lines.append("")
        
        # Procesează perechi (număr alineat, conținut alineat)
        for i in range(1, len(parts), 2):
            if i + 1 < len(parts):
                alineat_nr = parts[i]
                alineat_text = parts[i + 1].strip()
                
                # Formatează literele din alineat (dacă are)
                formatted_alineat = self._format_litere(alineat_text)
                
                # Pune alineatul bold pe linie separată, apoi conținutul
                formatted_lines.append(f"**({alineat_nr})**")
                formatted_lines.append(formatted_alineat)
                formatted_lines.append("")
        
        return "\n".join(formatted_lines).strip()
    
    def _format_litere(self, text: str) -> str:
        """
        Formatează literele a), b), c), ..., ș), ț) din text
        Pune fiecare literă pe rând nou și indentată
        
        Literele sunt marcate în HTML cu S_LIT_TTL și au separator ";..." între ele
        
        IMPORTANT: O enumerare reală începe întotdeauna cu litera a)
        Dacă textul conține doar referințe la litere (ex: "lit. d)") fără să înceapă 
        enumerarea cu a), atunci nu este o enumerare reală și nu trebuie formatat.
        
        Args:
            text: Text care poate conține litere
            
        Returns:
            Text cu litere formatate
        """
        if not text:
            return text
        
        # Verifică dacă are separatorul de litere ";..."
        if ';...' in text:
            logger.debug(f"_format_litere: Găsit separator ;... în text de lungime {len(text)}")
            
            # Verifică dacă există litera a) în text - indicator de enumerare reală
            # Pattern: a) urmat de orice caracter (nu necesită spațiu)
            # DAR nu precedat de "lit." sau "lit:" - acestea sunt referințe, nu enumerări
            a_match = re.search(r'a\)', text, re.IGNORECASE)
            if not a_match:
                # Nu are litera a) - probabil sunt doar referințe (ex: "lit. d)")
                logger.debug("_format_litere: Nu am găsit litera a) - nu este enumerare reală")
                return text.strip()
            
            # Verifică contextul din jurul lui a) pentru a determina dacă e referință sau enumerare
            start_pos = max(0, a_match.start() - 10)
            context_before = text[start_pos:a_match.start()].lower()
            
            # Dacă a) este precedat imediat de "lit." sau "lit:", e o referință, nu enumerare
            if re.search(r'lit\.?\s*$', context_before):
                logger.debug("_format_litere: a) este precedat de 'lit.' - este referință, nu enumerare")
                return text.strip()
            
            # Split pe ";..." pentru a separa literele
            parts = text.split(';...')
            formatted = []
            
            for i, part in enumerate(parts):
                part = part.strip()
                if not part:
                    continue
                
                if i == 0:
                    # Prima parte - poate conține introducerea + prima literă
                    # Caută prima literă în text
                    match = re.search(r'([a-zăâîșț]\))(.+)$', part, re.IGNORECASE | re.DOTALL)
                    if match:
                        # Are literă - separă introducerea de literă
                        intro_end = match.start()
                        if intro_end > 0:
                            intro = part[:intro_end].rstrip(':').strip()
                            if intro:
                                formatted.append(intro + ':')
                        
                        # Adaugă prima literă
                        litera = match.group(1)
                        litera_text = match.group(2).strip()
                        formatted.append(f"\n  **{litera}** {litera_text}")
                    else:
                        # Nu are literă - e doar introducere
                        intro = part.rstrip(':').strip()
                        if intro:
                            formatted.append(intro + ':')
                else:
                    # Părțile următoare - fiecare ar trebui să înceapă cu literă)
                    match = re.match(r'^([a-zăâîșț]\))\s*(.+)$', part, re.IGNORECASE | re.DOTALL)
                    
                    if match:
                        # E o literă
                        litera = match.group(1)
                        litera_text = match.group(2).strip()
                        formatted.append(f"\n  **{litera}** {litera_text}")
                    else:
                        # Nu e literă - text după ultima literă
                        if part and part not in [':', ';', '.', '...']:
                            formatted.append(f"\n\n{part}")
            
            return "".join(formatted) if formatted else text.strip()
        else:
            # Nu are ";..." - returnează textul neschimbat
            # Nu încercăm să detectăm litere standalone pentru că riscăm false positives
            return text.strip()
            
            return "".join(formatted) if formatted else text.strip()
    
    def _generate_markdown(self, df: pd.DataFrame) -> str:
        """
        Generează conținut Markdown optimizat pentru RAG și vector databases
        
        Args:
            df: DataFrame cu articolele parsate
            
        Returns:
            String cu conținutul Markdown structurat
        """
        if df.empty:
            return "# Document gol\n\nNu s-au găsit articole."
        
        lines = []
        
        # YAML Frontmatter - metadata globală
        first_row = df.iloc[0]
        lines.append("---")
        lines.append(f"tip_act: {first_row.get('tip_act', 'N/A')}")
        lines.append(f"nr_act: {first_row.get('nr_act', 'N/A')}")
        lines.append(f"data_act: {first_row.get('data_act', 'N/A')}")
        lines.append(f"an_act: {first_row.get('an_act', 'N/A')}")
        lines.append(f"emitent_act: {first_row.get('emitent_act', 'N/A')}")
        lines.append(f'titlu_act: "{first_row.get("titlu_act", "N/A")}"')
        lines.append(f"mof_nr: {first_row.get('mof_nr', 'N/A')}")
        lines.append(f"mof_data: {first_row.get('mof_data', 'N/A')}")
        lines.append(f"mof_an: {first_row.get('mof_an', 'N/A')}")
        lines.append(f"total_articole: {len(df)}")
        lines.append("---")
        lines.append("")
        
        # Titlu principal
        tip_act = first_row.get('tip_act', 'ACT NORMATIV')
        nr_act = first_row.get('nr_act', '')
        data_act = first_row.get('data_act', '')
        
        if nr_act:
            lines.append(f"# {tip_act} nr. {nr_act} din {data_act}")
        else:
            lines.append(f"# {tip_act} din {data_act}")
        lines.append("")
        
        if first_row.get('emitent_act'):
            lines.append(f"**Emitent:** {first_row.get('emitent_act')}")
        if first_row.get('mof_nr'):
            lines.append(f"**Publicat în:** Monitorul Oficial nr. {first_row.get('mof_nr')} din {first_row.get('mof_data')}")
        lines.append("")
        
        if first_row.get('titlu_act'):
            lines.append("## Titlu Act")
            lines.append(first_row.get('titlu_act'))
            lines.append("")
        
        lines.append("---")
        lines.append("")
        
        # INDEX STRUCTURAT
        lines.append("# INDEX")
        lines.append("")
        
        # Construiește index ierarhic
        current_titlu = None
        current_capitol = None
        current_sectiune = None
        current_subsectiune = None
        
        for idx, row in df.iterrows():
            # Construiește ierarhia din coloane
            titlu = ''
            capitol = ''
            sectiune = ''
            subsectiune = ''
            
            if row.get('titlu_denumire'):
                titlu_nr = row.get('titlu_nr', '')
                titlu_den = row.get('titlu_denumire', '')
                titlu = f"TITLUL {titlu_nr} - {titlu_den}" if titlu_nr else titlu_den
            
            if row.get('capitol_denumire'):
                capitol_nr = row.get('capitol_nr', '')
                capitol_den = row.get('capitol_denumire', '')
                capitol = f"CAPITOLUL {capitol_nr} - {capitol_den}" if capitol_nr else capitol_den
            
            if row.get('sectiune_denumire'):
                sectiune_nr = row.get('sectiune_nr', '')
                sectiune_den = row.get('sectiune_denumire', '')
                sectiune = f"SECȚIUNEA {sectiune_nr} - {sectiune_den}" if sectiune_nr else sectiune_den
            
            if row.get('subsectiune_denumire'):
                subsectiune_nr = row.get('subsectiune_nr', '')
                subsectiune_den = row.get('subsectiune_denumire', '')
                subsectiune = f"SUBSECȚIUNEA {subsectiune_nr} - {subsectiune_den}" if subsectiune_nr else subsectiune_den
            
            nr_articol = row.get('art_nr', row.get('nr_articol', ''))
            
            # Titlu nou
            if titlu and titlu != current_titlu:
                lines.append(f"## {titlu}")
                current_titlu = titlu
                current_capitol = None
                current_sectiune = None
                current_subsectiune = None
            
            # Capitol nou
            if capitol and capitol != current_capitol:
                lines.append(f"### {capitol}")
                current_capitol = capitol
                current_sectiune = None
                current_subsectiune = None
            
            # Secțiune nouă
            if sectiune and sectiune != current_sectiune:
                lines.append(f"#### {sectiune}")
                current_sectiune = sectiune
                current_subsectiune = None
            
            # Subsecțiune nouă
            if subsectiune and subsectiune != current_subsectiune:
                lines.append(f"##### {subsectiune}")
                current_subsectiune = subsectiune
            
            # Articol
            if nr_articol:
                lines.append(f"- [Art. {nr_articol}](#art-{nr_articol}) - *[Issue: TODO]*")
        
        lines.append("")
        lines.append("---")
        lines.append("")
        
        # CHUNKS - fiecare articol
        lines.append("# ARTICOLE")
        lines.append("")
        
        for idx, row in df.iterrows():
            nr_articol = row.get('art_nr', row.get('nr_articol', ''))
            text_articol = row.get('text_articol', '')
            
            # Construiește context ierarhic complet
            titlu = ''
            capitol = ''
            sectiune = ''
            
            # Verifică mai multe variante de nume coloane
            if row.get('titlu_denumire'):
                titlu_nr = row.get('titlu_nr', '')
                titlu_den = row.get('titlu_denumire', '')
                titlu = f"TITLUL {titlu_nr} - {titlu_den}" if titlu_nr else titlu_den
            elif row.get('titlu'):
                titlu = row.get('titlu')
            
            if row.get('capitol_denumire'):
                capitol_nr = row.get('capitol_nr', '')
                capitol_den = row.get('capitol_denumire', '')
                capitol = f"CAPITOLUL {capitol_nr} - {capitol_den}" if capitol_nr else capitol_den
            elif row.get('capitol'):
                capitol = row.get('capitol')
            
            if row.get('sectiune_denumire'):
                sectiune_nr = row.get('sectiune_nr', '')
                sectiune_den = row.get('sectiune_denumire', '')
                sectiune = f"SECȚIUNEA {sectiune_nr} - {sectiune_den}" if sectiune_nr else sectiune_den
            elif row.get('sectiune'):
                sectiune = row.get('sectiune')
            
            # Header articol
            if nr_articol:
                lines.append(f'<a id="art-{nr_articol}"></a>')
                lines.append(f"## Art. {nr_articol}")
            else:
                idx_num = int(idx) if isinstance(idx, (int, float)) else 0
                lines.append(f'<a id="art-{idx_num + 1}"></a>')
                lines.append(f"## Art. {idx_num + 1}")
            lines.append("")
            
            # Context ierarhic
            context_parts = []
            if titlu:
                context_parts.append(titlu)
            if capitol:
                context_parts.append(capitol)
            if sectiune:
                context_parts.append(sectiune)
            
            if context_parts:
                lines.append(f"**Context ierarhic:** {' / '.join(context_parts)}")
                lines.append("")
            
            # Issue placeholder
            lines.append("**Issue:** *[TODO - adaugă descriere scurtă]*")
            lines.append("")
            
            # Explicație placeholder
            lines.append("**Explicație:** *[TODO - adaugă explicație în 1-2 fraze, limbaj simplu]*")
            lines.append("")
            
            # Metadata structurată pentru embedding
            lines.append("**Metadata:**")
            lines.append("```yaml")
            lines.append(f"tip_element: articol")
            if nr_articol:
                lines.append(f"nr_articol: {nr_articol}")
            if titlu:
                lines.append(f"titlu: {titlu}")
            if capitol:
                lines.append(f"capitol: {capitol}")
            if sectiune:
                lines.append(f"sectiune: {sectiune}")
            lines.append(f"tip_act: {row.get('tip_act', 'N/A')}")
            lines.append(f"nr_act: {row.get('nr_act', 'N/A')}")
            lines.append(f"an_act: {row.get('an_act', 'N/A')}")
            lines.append(f"titlu_act: {row.get('titlu_act', 'N/A')}")
            lines.append("```")
            lines.append("")
            
            # Conținut articol
            lines.append("**Conținut:**")
            lines.append("")
            if text_articol:
                formatted_text = self._format_article_text(text_articol)
                lines.append(formatted_text)
            else:
                lines.append("*[Conținut lipsă]*")
            lines.append("")
            lines.append("---")
            lines.append("")
        
        return "\n".join(lines)
    
    def _generate_markdown_from_html(self, soup: BeautifulSoup, metadata: Dict[str, Any], df: Optional[pd.DataFrame] = None) -> str:
        """
        Generează Markdown direct din HTML, fără conversie prin DataFrame.
        Această metodă înlocuiește _generate_markdown() pentru o procesare mai directă și precisă.
        
        Args:
            soup: BeautifulSoup object cu HTML-ul parsat
            metadata: Metadata extrasă (tip_act, nr_act, data_act, etc.)
            df: DataFrame cu articolele (opțional, pentru a include issue în INDEX)
        
        Returns:
            String cu conținutul Markdown complet
        """
        lines = []
        
        # === YAML FRONTMATTER ===
        lines.append("---")
        lines.append(f"tip_act: {metadata.get('tip_act', 'N/A')}")
        lines.append(f"nr_act: {metadata.get('nr_act', 'N/A')}")
        lines.append(f"data_act: {metadata.get('data_act', 'N/A')}")
        
        # Extrage anul din data_act (ex: "30/04/2024" -> 2024)
        an_act = 'N/A'
        if metadata.get('data_act'):
            match = re.search(r'/(\d{4})$', metadata['data_act'])
            if match:
                an_act = match.group(1)
        lines.append(f"an_act: {an_act}")
        
        lines.append(f"emitent_act: {metadata.get('emitent_act', 'N/A')}")
        lines.append(f"titlu_act: {metadata.get('titlu_act', 'N/A')}")
        lines.append(f"mof_nr: {metadata.get('mof_nr', 'N/A')}")
        lines.append(f"mof_data: {metadata.get('mof_data', 'N/A')}")
        
        # Extrage anul MOF din mof_data
        mof_an = 'N/A'
        if metadata.get('mof_data'):
            match = re.search(r'/(\d{4})$', metadata['mof_data'])
            if match:
                mof_an = match.group(1)
        lines.append(f"mof_an: {mof_an}")
        
        # Numără total articole
        total_articole = len(soup.find_all(class_='S_ART_TTL'))
        lines.append(f"total_articole: {total_articole}")
        lines.append("---")
        lines.append("")
        
        # === HEADER ===
        lines.append(f"# {metadata.get('tip_act', 'ACT LEGISLATIV')} nr. {metadata.get('nr_act', 'N/A')} din {metadata.get('data_act', 'N/A')}")
        lines.append("")
        if metadata.get('emitent_act'):
            lines.append(f"**Emitent:** {metadata['emitent_act']}")
            lines.append("")
        if metadata.get('mof_nr') and metadata.get('mof_data'):
            lines.append(f"**Publicat în:** Monitorul Oficial nr. {metadata['mof_nr']} din {metadata['mof_data']}")
            lines.append("")
        if metadata.get('titlu_act'):
            lines.append(f"**Titlu:** {metadata['titlu_act']}")
            lines.append("")
        
        # === INDEX IERARHIC ===
        lines.append("## INDEX")
        lines.append("")
        
        # Construiește INDEX din structura HTML (cu issue din DataFrame)
        index_lines = self._build_index_from_html(soup, df)
        lines.extend(index_lines)
        lines.append("")
        
        # === ARTICOLE ===
        lines.append("## ARTICOLE")
        lines.append("")
        
        # Procesează fiecare articol direct din HTML
        article_lines = self._build_articles_from_html(soup, metadata)
        lines.extend(article_lines)
        
        return "\n".join(lines)
    
    def _build_index_from_html(self, soup: BeautifulSoup, df: Optional[pd.DataFrame] = None) -> List[str]:
        """
        Construiește INDEX-ul ierarhic direct din HTML.
        Detectează TITLURI, CAPITOLE, SECȚIUNI, SUBSECȚIUNI și articole.
        Include și textul issue din DataFrame pentru fiecare articol.
        
        Args:
            soup: BeautifulSoup object cu HTML-ul
            df: DataFrame cu articolele (opțional, pentru a include issue)
        """
        lines = []
        
        # Context ierarhic curent
        current_titlu = None
        current_capitol = None
        current_sectiune = None
        
        # Creează dicționar pentru lookup rapid issue by article number
        issue_map = {}
        if df is not None and 'issue' in df.columns:
            # Caută coloana cu numărul articolului
            nr_col = None
            for col in ['Articol_Nr', 'nr_articol', 'Articol', 'articol']:
                if col in df.columns:
                    nr_col = col
                    break
            
            if nr_col:
                for _, row in df.iterrows():
                    art_nr = row.get(nr_col)
                    issue_text = row.get('issue', '')
                    
                    # Convertește numărul articolului la string
                    if pd.notna(art_nr):
                        try:
                            art_nr_str = str(int(art_nr))
                            if pd.notna(issue_text) and issue_text and issue_text != '*[TODO - adaugă descriere scurtă]*':
                                issue_map[art_nr_str] = str(issue_text)
                        except (ValueError, TypeError):
                            pass
        
        # Găsește toate elementele de structură în ordine
        for element in soup.find_all(class_=re.compile(r'S_(TTL|CAP|SEC|ART)_TTL')):
            classes = element.get('class', [])
            text = element.get_text(strip=True)
            
            # TITLURI (S_TTL_TTL)
            if 'S_TTL_TTL' in classes:
                current_titlu = text
                current_capitol = None
                current_sectiune = None
                lines.append(f"### {text}")
                
            # CAPITOLE (S_CAP_TTL)
            elif 'S_CAP_TTL' in classes:
                current_capitol = text
                current_sectiune = None
                
                # Găsește denumirea capitolului (S_CAP_DEN)
                den_elem = element.find_next_sibling(class_='S_CAP_DEN')
                if den_elem:
                    capitol_full = f"{text} - {den_elem.get_text(strip=True)}"
                else:
                    capitol_full = text
                
                if current_titlu:
                    lines.append(f"#### {capitol_full}")
                else:
                    lines.append(f"### {capitol_full}")
            
            # SECȚIUNI (S_SEC_TTL)
            elif 'S_SEC_TTL' in classes:
                current_sectiune = text
                
                # Găsește denumirea secțiunii (S_SEC_DEN)
                den_elem = element.find_next_sibling(class_='S_SEC_DEN')
                if den_elem:
                    sectiune_full = f"{text} - {den_elem.get_text(strip=True)}"
                else:
                    sectiune_full = text
                
                if current_capitol:
                    lines.append(f"##### {sectiune_full}")
                elif current_titlu:
                    lines.append(f"#### {sectiune_full}")
                else:
                    lines.append(f"### {sectiune_full}")
            
            # ARTICOLE (S_ART_TTL)
            elif 'S_ART_TTL' in classes:
                # Extrage numărul articolului
                match = re.search(r'articol(ul)?\s+(\d+)', text, re.I)
                if match:
                    art_nr = match.group(2)
                    
                    # Construiește linia INDEX cu issue dacă există
                    if art_nr in issue_map:
                        lines.append(f"- [Articolul {art_nr}](#articolul-{art_nr}) - {issue_map[art_nr]}")
                    else:
                        lines.append(f"- [Articolul {art_nr}](#articolul-{art_nr})")
        
        return lines
    
    def _build_articles_from_html(self, soup: BeautifulSoup, metadata: Dict[str, Any]) -> List[str]:
        """
        Construiește secțiunea ARTICOLE direct din HTML.
        Pentru fiecare articol: context ierarhic, issue, explicație, metadata, conținut.
        """
        lines = []
        
        # Context ierarhic curent
        context = {
            'titlu': None,
            'capitol': None,
            'sectiune': None,
            'subsectiune': None
        }
        
        # Iterează prin toate elementele pentru a construi context și extrage articole
        for element in soup.find_all(class_=re.compile(r'S_(TTL|CAP|SEC|ART)_TTL')):
            classes = element.get('class', [])
            text = element.get_text(strip=True)
            
            # Actualizează context
            if 'S_TTL_TTL' in classes:
                context['titlu'] = text
                context['capitol'] = None
                context['sectiune'] = None
                context['subsectiune'] = None
                
            elif 'S_CAP_TTL' in classes:
                den_elem = element.find_next_sibling(class_='S_CAP_DEN')
                if den_elem:
                    context['capitol'] = f"{text} - {den_elem.get_text(strip=True)}"
                else:
                    context['capitol'] = text
                context['sectiune'] = None
                context['subsectiune'] = None
                
            elif 'S_SEC_TTL' in classes:
                den_elem = element.find_next_sibling(class_='S_SEC_DEN')
                if den_elem:
                    context['sectiune'] = f"{text} - {den_elem.get_text(strip=True)}"
                else:
                    context['sectiune'] = text
                context['subsectiune'] = None
            
            # Procesează ARTICOL
            elif 'S_ART_TTL' in classes:
                # Extrage numărul articolului
                match = re.search(r'articol(ul)?\s+(\d+)', text, re.I)
                if not match:
                    continue
                
                art_nr = match.group(2)
                
                # Header articol
                lines.append(f"### Articolul {art_nr}")
                lines.append("")
                
                # Context ierarhic
                lines.append("**Context ierarhic:**")
                if context['titlu']:
                    lines.append(f"- **Titlu:** {context['titlu']}")
                if context['capitol']:
                    lines.append(f"- **Capitol:** {context['capitol']}")
                if context['sectiune']:
                    lines.append(f"- **Secțiune:** {context['sectiune']}")
                if context['subsectiune']:
                    lines.append(f"- **Subsecțiune:** {context['subsectiune']}")
                lines.append("")
                
                # Issue placeholder
                lines.append("**Issue:** *[TODO - adaugă descriere scurtă]*")
                lines.append("")
                
                # Explicație placeholder
                lines.append("**Explicație:** *[TODO - adaugă explicație în 1-2 fraze, limbaj simplu]*")
                lines.append("")
                
                # Metadata YAML
                lines.append("**Metadata:**")
                lines.append("```yaml")
                lines.append(f"tip_element: articol")
                lines.append(f"nr_articol: {art_nr}")
                if context['titlu']:
                    lines.append(f"titlu: {context['titlu']}")
                if context['capitol']:
                    lines.append(f"capitol: {context['capitol']}")
                if context['sectiune']:
                    lines.append(f"sectiune: {context['sectiune']}")
                lines.append(f"tip_act: {metadata.get('tip_act', 'N/A')}")
                lines.append(f"nr_act: {metadata.get('nr_act', 'N/A')}")
                
                # Extrage anul din data_act
                an_act = 'N/A'
                if metadata.get('data_act'):
                    match_an = re.search(r'/(\d{4})$', metadata['data_act'])
                    if match_an:
                        an_act = match_an.group(1)
                lines.append(f"an_act: {an_act}")
                lines.append(f"titlu_act: {metadata.get('titlu_act', 'N/A')}")
                lines.append("```")
                lines.append("")
                
                # Conținut articol (extrage din HTML)
                lines.append("**Conținut:**")
                lines.append("")
                
                article_content = self._extract_article_content_from_html(element)
                if article_content:
                    lines.append(article_content)
                else:
                    lines.append("*[Conținut lipsă]*")
                
                lines.append("")
                lines.append("---")
                lines.append("")
        
        return lines
    
    def _normalize_legislative_text(self, text: str) -> str:
        """
        Normalizează textul legislativ adăugând spații înainte de referințe legislative
        care au fost unite greșit în HTML-ul original.
        
        Exemple:
        - "laalin. (1)" -> "la alin. (1)"
        - "lalit. a)" -> "la lit. a)"
        - "lacap. II" -> "la cap. II"
        - "prevederilorart. 10" -> "prevederilor art. 10"
        - "(1)se" -> "(1) se"
        - "a)șib)" -> "a) și b)"
        """
        # Pattern pentru referințe legislative fără spații
        # Caută cuvinte urmate direct de "alin.", "lit.", "cap.", "art.", etc.
        patterns = [
            (r'(\w)(alin\.)', r'\1 \2'),      # "laalin." -> "la alin."
            (r'(\w)(lit\.)', r'\1 \2'),       # "lalit." -> "la lit."
            (r'(\w)(cap\.)', r'\1 \2'),       # "lacap." -> "la cap."
            (r'(\w)(art\.)', r'\1 \2'),       # "laart." -> "la art."
            (r'(\w)(pct\.)', r'\1 \2'),       # "lapct." -> "la pct."
            (r'(\w)(sec[țt]\.)', r'\1 \2'),   # "lasecț." -> "la secț."
            (r'(\w)(tit\.)', r'\1 \2'),       # "latit." -> "la tit."
            (r'(\w)(par\.)', r'\1 \2'),       # "lapar." -> "la par."
            # Adaugă spații după paranteze/litere urmate de cuvinte
            (r'\)([a-zăâîșțA-ZĂÂÎȘȚ])', r') \1'),  # "(1)se" -> "(1) se", "b)șic)" -> "b) șic)"
            (r'(și|sau|de|cu|la|în|pentru|ca|dacă)([a-z]\))', r'\1 \2'),  # "șib)" -> "și b)", "saue)" -> "sau e)"
        ]
        
        normalized = text
        for pattern, replacement in patterns:
            normalized = re.sub(pattern, replacement, normalized)
        
        return normalized
    
    def _extract_article_content_from_html(self, art_ttl_element) -> str:
        """
        Extrage și formatează conținutul articolului direct din HTML.
        Procesează S_ALN (alineate) și S_LIT (litere) cu formatare Markdown.
        
        Formatare:
        - Alineate: **(1)** pe linie separată, conținut pe linia următoare
        - Litere (enumeration): **a)**, **b)**, **c)** indentate cu 2 spații
        - Litere (referință): "lit. a)-c)" rămâne în text, NU se formatează
        """
        lines = []
        
        # Găsește S_ART_BDY (corpul articolului)
        art_bdy = None
        for sibling in art_ttl_element.find_next_siblings():
            if 'S_ART_BDY' in sibling.get('class', []):
                art_bdy = sibling
                break
            # Oprește-te dacă găsești un nou articol
            if 'S_ART_TTL' in sibling.get('class', []):
                break
        
        if not art_bdy:
            return ""
        
        # Verifică dacă există structură cu PARAGRAFE + PUNCTE (caz special)
        par_elements = art_bdy.find_all(class_=re.compile(r'S_PAR'), recursive=False)
        has_par_with_pct = False
        
        if par_elements:
            for par in par_elements:
                if par.find_all(class_=re.compile(r'S_PCT')):
                    has_par_with_pct = True
                    break
        
        if has_par_with_pct:
            # CAZ SPECIAL: Paragraf introductiv + puncte
            for par in par_elements:
                # Text introductiv (direct children doar)
                intro_texts = []
                for child in par.children:
                    if isinstance(child, str):
                        text = child.strip()
                        if text:
                            intro_texts.append(text)
                
                if intro_texts:
                    lines.append(' '.join(intro_texts))
                    lines.append("")
                
                # Procesează punctele
                puncte = par.find_all(class_=re.compile(r'S_PCT'))
                for pct in puncte:
                    ttl = pct.find(class_=re.compile(r'S_PCT_TTL'))
                    bdy = pct.find(class_=re.compile(r'S_PCT_BDY'))
                    
                    if ttl and bdy:
                        numero = ttl.get_text(strip=True)
                        text = self._normalize_legislative_text(bdy.get_text(strip=True))
                        if numero and text:
                            lines.append(f"{numero} {text}")
            
            return "\n".join(lines)
        
        # Procesează ALINEATE (S_ALN) - structură normală
        alineate = art_bdy.find_all(class_=re.compile(r'S_ALN'), recursive=False)
        
        if alineate:
            for aln in alineate:
                # Găsește S_ALN_TTL (numărul alineatului) și S_ALN_BDY (conținutul)
                ttl = aln.find(class_=re.compile(r'S_ALN_TTL'))
                bdy = aln.find(class_=re.compile(r'S_ALN_BDY'))
                
                if ttl and bdy:
                    numero = ttl.get_text(strip=True)  # Ex: "(1)"
                    
                    # Formatează numărul alineatului pe linie separată
                    lines.append(f"**{numero}**")
                    lines.append("")
                    
                    # Verifică dacă alineatul conține LITERE (S_LIT)
                    litere = bdy.find_all(class_=re.compile(r'S_LIT'), recursive=False)
                    
                    if litere:
                        # Extrage textul introductiv (înainte de litere)
                        intro_texts = []
                        for child in bdy.children:
                            if isinstance(child, str):
                                text = child.strip()
                                if text:
                                    intro_texts.append(self._normalize_legislative_text(text))
                            elif child.name and 'S_LIT' not in child.get('class', []):
                                # Text din alte elemente (nu S_LIT)
                                text = self._normalize_legislative_text(child.get_text(strip=True))
                                if text:
                                    intro_texts.append(text)
                        
                        if intro_texts:
                            lines.append(' '.join(intro_texts))
                            lines.append("")
                        
                        # Procesează fiecare literă
                        for lit in litere:
                            lit_ttl = lit.find(class_=re.compile(r'S_LIT_TTL'))
                            lit_bdy = lit.find(class_=re.compile(r'S_LIT_BDY'))
                            
                            if lit_ttl and lit_bdy:
                                litera = lit_ttl.get_text(strip=True)  # Ex: "a)"
                                text = self._normalize_legislative_text(lit_bdy.get_text(strip=True))
                                
                                if litera and text:
                                    # Formatează litera cu indentare
                                    lines.append(f"  **{litera}** {text}")
                    else:
                        # Alineat simplu, fără litere
                        text = self._normalize_legislative_text(bdy.get_text(strip=True))
                        if text:
                            lines.append(text)
                    
                    lines.append("")
            
            return "\n".join(lines)
        
        # FALLBACK: Paragraf simplu (S_PAR) - poate conține litere (S_LIT)
        paragrafe = art_bdy.find_all(class_=re.compile(r'S_PAR'))
        if paragrafe:
            for par in paragrafe:
                # Verifică dacă paragraful conține LITERE (S_LIT)
                litere = par.find_all(class_=re.compile(r'S_LIT'), recursive=False)
                
                if litere:
                    # Paragraf cu enumerare de litere
                    # Extrage textul introductiv (înainte de litere)
                    intro_texts = []
                    for child in par.children:
                        if isinstance(child, str):
                            text = child.strip()
                            if text:
                                intro_texts.append(self._normalize_legislative_text(text))
                        elif child.name and 'S_LIT' not in child.get('class', []):
                            # Text din alte elemente (nu S_LIT)
                            text = self._normalize_legislative_text(child.get_text(strip=True))
                            if text:
                                intro_texts.append(text)
                    
                    if intro_texts:
                        lines.append(' '.join(intro_texts))
                        lines.append("")
                    
                    # Procesează fiecare literă
                    for lit in litere:
                        lit_ttl = lit.find(class_=re.compile(r'S_LIT_TTL'))
                        lit_bdy = lit.find(class_=re.compile(r'S_LIT_BDY'))
                        
                        if lit_ttl and lit_bdy:
                            litera = lit_ttl.get_text(strip=True)  # Ex: "a)"
                            text = self._normalize_legislative_text(lit_bdy.get_text(strip=True))
                            
                            if litera and text:
                                # Formatează litera cu indentare (2 spații)
                                lines.append(f"  **{litera}** {text}")
                else:
                    # Paragraf simplu fără litere
                    text = self._normalize_legislative_text(par.get_text(strip=True))
                    if text:
                        lines.append(text)
                
                lines.append("")
            
            return "\n".join(lines)
        
        # ULTIMUL FALLBACK: Tot textul
        text = self._normalize_legislative_text(art_bdy.get_text(separator='\n', strip=True))
        return text if text else ""
    
    def save_to_rezultate(self, df: pd.DataFrame, filename_prefix: str = 'parsed', 
                          metrics: Optional[Dict[str, Any]] = None) -> Dict[str, str]:
        """
        Salvează rezultatele în folderul 'rezultate' în format CSV și Markdown
        
        Args:
            df: DataFrame cu rezultate
            filename_prefix: Prefix pentru numele fișierelor (nu se folosește)
            metrics: Metrics din parsare (opțional, pentru validation)
        
        Returns:
            Dict cu căile fișierelor salvate
        """
        # Creează folderul rezultate dacă nu există
        os.makedirs('rezultate', exist_ok=True)
        
        # Generează timestamp pentru nume unice
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        
        # Extrage metadata pentru nume fișier: Legea_123_2025_timestamp
        filename = 'act_legislativ'
        if not df.empty and 'tip_act' in df.columns:
            first_row = df.iloc[0]
            tip_act = first_row.get('tip_act', '')
            nr_act = first_row.get('nr_act', '')
            an_act = first_row.get('an_act', '')
            
            if tip_act:
                # Normalizează tipul actului pentru numele fișierului
                tip_normalized = tip_act.replace(' ', '_').replace('Ă', 'A').replace('Â', 'A').replace('Ț', 'T').replace('Ș', 'S')
                filename_parts = [tip_normalized]
                
                if nr_act:
                    filename_parts.append(str(nr_act))
                
                if an_act:
                    filename_parts.append(str(an_act))
                
                filename = '_'.join(filename_parts)
        
        saved_files = {}
        
        try:
            # Salvează CSV
            csv_path = os.path.join('rezultate', f'{filename}_{timestamp}.csv')
            df.to_csv(csv_path, index=False, encoding='utf-8')
            saved_files['csv'] = csv_path
            logger.info(f"✅ CSV salvat în: {csv_path}")
            
            # Salvează Markdown folosind metoda nouă (direct din HTML)
            md_path = os.path.join('rezultate', f'{filename}_{timestamp}.md')
            
            # Folosește noua metodă _generate_markdown_from_html() dacă avem HTML salvat
            if self.last_soup and self.last_metadata:
                logger.info("📝 Generez Markdown direct din HTML...")
                md_content = self._generate_markdown_from_html(self.last_soup, self.last_metadata, df)
            else:
                # Fallback la metoda veche (din DataFrame)
                logger.warning("⚠️ Nu am HTML salvat, folosesc metoda veche (din DataFrame)")
                md_content = self._generate_markdown(df)
            
            with open(md_path, 'w', encoding='utf-8') as f:
                f.write(md_content)
            saved_files['markdown'] = md_path
            logger.info(f"✅ Markdown salvat în: {md_path}")
            
        except Exception as e:
            logger.error(f"❌ Eroare la salvare: {e}")
        
        return saved_files
