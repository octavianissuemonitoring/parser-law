#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Parser HTML robuest pentru structura legislativă de pe legislatie.just.ro
Folosește clasele CSS specifice pentru extragere precisă
"""

import re
import pandas as pd
from typing import List, Dict, Tuple, Optional, Any
from bs4 import BeautifulSoup
from config import TIPURI_ACTE_NORMATIVE

# Mapare clase CSS -> tipuri de elemente (doar clase utilizate efectiv)
CLASS_MAPPING = {
    # Articole
    'S_ART_TTL': 'articol_titlu',
    'S_ART_BDY': 'articol_corp',
    'S_ART': 'articol_general',
    
    # Capitole
    'S_CAP_TTL': 'capitol_titlu',
    'S_CAP_DEN': 'capitol_denumire',
    'S_CAP': 'capitol_general',
    
    # Secțiuni
    'S_SEC_TTL': 'sectiune_titlu',
    'S_SEC_DEN': 'sectiune_denumire',
    'S_SEC': 'sectiune_general',
    
    # Alineate
    'S_ALN_TTL': 'alineat_titlu',
    'S_ALN_BDY': 'alineat_corp',
    'S_ALN': 'alineat_general',
    
    # Litere
    'S_LIT_TTL': 'litera_titlu',
    'S_LIT_BDY': 'litera_corp',
    'S_LIT': 'litera_general',
    
    # Puncte și paragrafe
    'S_PCT_TTL': 'punct_titlu',
    'S_PCT_BDY': 'punct_corp',
    'S_PCT': 'punct_general',
    'S_PUB_TTL': 'publicatie_titlu',
    'S_PUB_BDY': 'publicatie_corp',
    'S_PAR': 'paragraf',
    
    # Titluri de nivel superior
    'S_TTL': 'titlu_general',
    'S_TTL_TTL': 'titlu_numar',
    'S_TTL_DEN': 'titlu_denumire',
    'S_TTL_BDY': 'titlu_corp',
    
    # Emitent
    'S_EMT_TTL': 'emitent_titlu',
    'S_EMT_BDY': 'emitent_corp',
    'S_EMT': 'emitent_general',
    
    # Header și metadata
    'S_HDR': 'header',
    'S_DEN': 'denumire'
}

def extract_number_from_text(text: str) -> Optional[int]:
    """Extrage primul număr dintr-un text"""
    match = re.search(r'\b(\d+)\b', text)
    return int(match.group(1)) if match else None

def extract_roman_from_text(text: str) -> Optional[int]:
    """Extrage și convertește primul număr roman dintr-un text"""
    roman_pattern = r'\b([IVXLCDM]+)\b'
    match = re.search(roman_pattern, text)
    if not match:
        return None
    
    roman = match.group(1)
    roman_map = {"I":1,"V":5,"X":10,"L":50,"C":100,"D":500,"M":1000}
    total = 0
    prev = 0
    
    for ch in reversed(roman):
        val = roman_map.get(ch, 0)
        if val < prev:
            total -= val
        else:
            total += val
            prev = val
    
    return total if total > 0 else None

def parse_html_legislative_structure(html_content: str) -> pd.DataFrame:
    """
    Parsează HTML-ul folosind clasele CSS specifice legislatie.just.ro
    
    Args:
        html_content: Conținutul HTML al paginii
        
    Returns:
        DataFrame cu structura legislativă parsată
    """
    soup = BeautifulSoup(html_content, 'html.parser')
    
    try:
        # Folosește strategia principală care funcționează perfect
        result = parse_with_specific_classes(soup)
        
        if result and len(result) > 0:
            df = pd.DataFrame(result)
            confidence = calculate_confidence(result)
            df['confidence_score'] = confidence
            print(f"Parsare reusita: {len(result)} articole, confidence {confidence:.2f}")
            return df
        else:
            print("Nu s-au gasit articole in document")
            return pd.DataFrame()
            
    except Exception as e:
        print(f"Eroare la parsare: {e}")
        return pd.DataFrame()

def parse_with_specific_classes(soup: BeautifulSoup) -> List[Dict]:
    """
    Strategia principală: folosește clasele CSS specifice identificate
    """
    rows = []
    metadata = extract_basic_metadata(soup)
    
    context = {
        'titlu_nr': None, 'titlu_den': None,
        'capitol_nr': None, 'capitol_den': None,
        'sectiune_nr': None, 'sectiune_den': None,
        'subsectiune_nr': None, 'subsectiune_den': None
    }
    
    # Parcurge toate elementele în ordinea DOM
    for element in soup.find_all(class_=re.compile(r'^S_')):
        element_classes = element.get('class') or []
        # Asigură-te că element_classes este o listă
        if isinstance(element_classes, str):
            element_classes = [element_classes]
        elif not isinstance(element_classes, list):
            element_classes = []
            
        element_type = classify_element(element_classes)
        text_content = element.get_text(strip=True)
        
        if not text_content:
            continue
            
        # Actualizează contextul structural
        update_context_from_element(context, element_type, text_content)
        
        # Extrage articole
        if element_type in ['articol_titlu', 'articol_general']:
            article_data = extract_article_from_element(element, context, metadata)
            if article_data:
                rows.append(article_data)
    
    return rows


def calculate_confidence(results: List[Dict]) -> float:
    """
    Calculează confidence score pentru rezultatele parsării
    
    Weights ajustate pentru a reflecta mai bine calitatea extracției:
    - Articolele sunt cel mai important indicator (0.5)
    - Structura este opțională (0.2) - multe documente simple nu au capitole
    - Conținutul și metadata sunt importante (0.2 + 0.1)
    """
    if not results:
        return 0.0
    
    score = 0.0
    weights = {
        'has_articles': 0.5,      # Are articole identificate (crescut de la 0.4)
        'has_structure': 0.2,     # Are structură - opțional (redus de la 0.3)
        'has_content': 0.2,       # Are conținut substanțial
        'has_metadata': 0.1       # Are metadata (tip act, număr, etc.)
    }
    
    # Verifică dacă are articole
    articles = [r for r in results if 'Articol_Label' in r and r['Articol_Label']]
    if articles:
        score += weights['has_articles']
    
    # Verifică structura
    has_chapters = any(r.get('Capitol_Nr') for r in results)
    has_sections = any(r.get('Sectiune_Nr') for r in results)
    if has_chapters or has_sections:
        score += weights['has_structure']
    
    # Verifică conținutul
    avg_content_length = sum(len(r.get('Text_Articol', '')) for r in results) / len(results)
    if avg_content_length > 50:
        score += weights['has_content']
    
    # Verifică metadata
    has_act_type = any(r.get('Tip_Act') for r in results)
    has_act_number = any(r.get('Nr') for r in results)
    if has_act_type or has_act_number:
        score += weights['has_metadata']
    
    return score
    context: Dict[str, Any] = {
        'titlu_nr': None, 'titlu_den': None,
        'capitol_nr': None, 'capitol_den': None,
        'sectiune_nr': None, 'sectiune_den': None,
        'subsectiune_nr': None, 'subsectiune_den': None
    }
    
    rows = []
    
    # Găsește toate elementele cu clase relevante, în ordine de apariție
    elements = soup.find_all(class_=re.compile(r'S_(TTL|ART|CAP|SEC|ALN|LIT|PUB|PAR|EMT|HDR|DEN)'))
    
    current_article = None
    article_parts = []
    
    for element in elements:
        element_classes = element.get('class') or []
        if not isinstance(element_classes, list):
            element_classes = [element_classes] if element_classes else []
        element_type = classify_element(element_classes)
        text = element.get_text(strip=True)
        
        if not text:
            continue
            
        # Procesează în funcție de tipul elementului
        if element_type == 'titlu_numar':
            # Flush articolul curent
            if current_article:
                save_article(current_article, article_parts, context, metadata, rows)
                current_article = None
                article_parts = []
            
            # Actualizează contextul titlu - extrage numărul
            titlu_nr = extract_roman_from_text(text)
            context['titlu_nr'] = titlu_nr
            # Nu setăm denumirea aici, o vom lua din S_TTL_DEN
            # Reset capitole și secțiuni când schimbăm titlul
            context['capitol_nr'] = None
            context['capitol_den'] = None
            context['sectiune_nr'] = None
            context['sectiune_den'] = None
            
        elif element_type == 'titlu_denumire':
            # Setăm denumirea titlului din S_TTL_DEN
            context['titlu_den'] = text.strip()
            
        elif element_type == 'capitol_titlu':
            # Flush articolul curent
            if current_article:
                save_article(current_article, article_parts, context, metadata, rows)
                current_article = None
                article_parts = []
            
            # Actualizează contextul capitol
            cap_nr = extract_roman_from_text(text) or extract_number_from_text(text)
            context['capitol_nr'] = cap_nr
            # Nu setăm denumirea aici, o vom lua din S_CAP_DEN
            # Reset secțiuni când schimbăm capitolul
            context['sectiune_nr'] = None
            context['sectiune_den'] = None
            
        elif element_type == 'capitol_denumire':
            # Setăm denumirea capitolului din S_CAP_DEN
            context['capitol_den'] = text.strip()
            
        elif element_type == 'sectiune_titlu':
            # Flush articolul curent
            if current_article:
                save_article(current_article, article_parts, context, metadata, rows)
                current_article = None
                article_parts = []
            
            # Actualizează contextul secțiune
            sec_nr = extract_number_from_text(text)
            context['sectiune_nr'] = sec_nr
            # Nu setăm denumirea aici, o vom lua din S_SEC_DEN
            
        elif element_type == 'sectiune_denumire':
            # Setăm denumirea secțiunii din S_SEC_DEN
            context['sectiune_den'] = text.strip()
            
        elif element_type == 'articol_titlu':
            # Flush articolul anterior
            if current_article:
                save_article(current_article, article_parts, context, metadata, rows)
            
            # Începe articol nou - salvăm și elementul pentru extragere ulterioară
            art_nr = extract_number_from_text(text)
            current_article = {
                'nr': art_nr,
                'label': text,
                'id': element.get('id', ''),
                'element': element  # Salvăm elementul pentru extract_article_content
            }
            article_parts = []
            
        elif element_type in ['articol_corp', 'alineat_corp', 'litera_corp', 'punct_corp']:
            # NU mai adăugăm manual - va fi extras de extract_article_content()
            pass
    
    # Flush ultimul articol
    if current_article:
        save_article(current_article, article_parts, context, metadata, rows)
    
    # Creează DataFrame
    df = pd.DataFrame(rows)
    
    if not df.empty:
        # Sortează și curăță
        sort_columns = ['Capitol_Nr', 'Sectiune_Nr', 'Art.1', 'Art.2']
        existing_cols = [col for col in sort_columns if col in df.columns]
        
        for col in existing_cols:
            # Convertește la numeric, păstrând None pentru valorile invalid
            df[col] = pd.to_numeric(df[col], errors='coerce')
            # NU folosim fillna(0) - păstrăm None pentru articole fără structură
            # Doar pentru sortare, înlocuim temporar None cu 0
            
        if existing_cols:
            # Sortare: temporar înlocuim None cu 0 doar pentru sort
            df_sort = df[existing_cols].fillna(0)
            df = df.loc[df_sort.sort_values(by=existing_cols).index].reset_index(drop=True)
    
    return df

def classify_element(classes: List[str]) -> Optional[str]:
    """Clasifică un element pe baza claselor CSS"""
    for cls in classes:
        if cls in CLASS_MAPPING:
            return CLASS_MAPPING[cls]
    return None

def convert_month_to_number(luna: str) -> str:
    """Convertește luna din text în număr (01-12)"""
    luni_map = {
        'ianuarie': '01', 'februarie': '02', 'martie': '03', 'aprilie': '04',
        'mai': '05', 'iunie': '06', 'iulie': '07', 'august': '08',
        'septembrie': '09', 'octombrie': '10', 'noiembrie': '11', 'decembrie': '12'
    }
    return luni_map.get(luna.lower(), luna)

def extract_basic_metadata(soup: BeautifulSoup) -> Dict[str, Any]:
    """Extrage metadata de bază din pagină"""
    metadata: Dict[str, Any] = {
        'tip_act': None, 
        'nr_act': None, 
        'data_act': None, 
        'denumire': None, 
        'mof_nr': None, 
        'mof_data': None
    }
    
    # Mai întâi încearcă să extragă din S_DEN (mai precis)
    s_den = soup.find(class_='S_DEN')
    if s_den:
        den_text = s_den.get_text(strip=True)
        # Pattern pentru S_DEN: "LEGE nr. 123 din 30 aprilie 2024" sau "METODOLOGIE din 29 iulie 2025"
        patterns_den = [
            r'(LEGE|ORDONANȚ[AĂ]\s+DE\s+URGEN[TȚ][AĂ]|ORDONANȚ[AĂ]|HOT[AĂ]R[ÂÎ]RE|DECRET|ORDIN|REGULAMENT|NORM[AĂ]|INSTRUC[TȚ]IUNE|METODOLOGIE)\s+nr\.?\s*(\d+)\s+din\s+(\d{1,2})\s+(\w+)\s+(\d{4})',
            r'(LEGE|ORDONANȚ[AĂ]\s+DE\s+URGEN[TȚ][AĂ]|ORDONANȚ[AĂ]|HOT[AĂ]R[ÂÎ]RE|DECRET|ORDIN|REGULAMENT|NORM[AĂ]|INSTRUC[TȚ]IUNE|METODOLOGIE)\s+nr\.?\s*(\d+)/(\d{4})',
            r'(METODOLOGIE|REGULAMENT|NORM[AĂ]|INSTRUC[TȚ]IUNE)\s+din\s+(\d{1,2})\s+(\w+)\s+(\d{4})'
        ]
        
        for pattern_idx, pattern in enumerate(patterns_den):
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
                    luna_nr = convert_month_to_number(luna)
                    metadata['data_act'] = f"{zi.zfill(2)}/{luna_nr}/{an}"
                else:
                    # Pattern 1 și 2 (cu număr)
                    metadata['nr_act'] = match.group(2)
                    # Extrage data - dacă are luna în text sau doar an
                    if len(match.groups()) >= 5:
                        zi = match.group(3)
                        luna = match.group(4)
                        an = match.group(5)
                        luna_nr = convert_month_to_number(luna)
                        metadata['data_act'] = f"{zi.zfill(2)}/{luna_nr}/{an}"
                    else:
                        metadata['data_act'] = match.group(3)
                break
    
    # Dacă nu s-a găsit în S_DEN, încearcă din title
    if not metadata['tip_act']:
        title = soup.find('title')
        if title:
            title_text = title.get_text(strip=True)
            # Parsează titlul pentru informații de bază
            patterns = [
                r'(LEGE|ORDONANȚ[AĂ]\s+DE\s+URGEN[TȚ][AĂ]|ORDONANȚ[AĂ]|HOT[AĂ]R[ÂÎ]RE|DECRET|ORDIN|REGULAMENT|NORM[AĂ]|INSTRUC[TȚ]IUNE|METODOLOGIE)\s+(\w+\s+)?(\d+)\s*/?\s*(\d{4})',
                r'(Legea|Ordonan[țt]a\s+de\s+urgen[țt][ăa]|Ordonan[țt]a|Hot[ăa]r[âî]rea|Decretul|Ordinul|Regulamentul|Norma|Instruc[țt]iunea|Metodologia)\s+nr\.?\s*(\d+)\s*/\s*(\d{4})'
            ]
            
            for pattern in patterns:
                match = re.search(pattern, title_text, re.IGNORECASE)
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
                    metadata['nr_act'] = match.group(2) if len(match.groups()) > 2 else match.group(-2)
                    metadata['data_act'] = match.group(-1)
                    break
    
    return metadata

def save_article(article: Dict, parts: List[str], context: Dict[str, Any], metadata: Dict[str, Any], rows: List[Dict]):
    """Salvează un articol în lista de rânduri"""
    # Extrage conținutul folosind extract_article_content dacă avem elementul
    if 'element' in article and article['element']:
        text_content = extract_article_content(article['element'])
    else:
        # Fallback pentru compatibilitate
        text_content = '\n'.join(parts).strip()
    
    row = {
        'Mof_nr': metadata.get('mof_nr'),
        'Mof_Data': metadata.get('mof_data'),
        'Mof_An': None,
        'Emitent': None,
        'Tip_Act': metadata.get('tip_act'),
        'Nr': metadata.get('nr_act'),
        'Data_An': metadata.get('data_act'),
        'Denumire': metadata.get('denumire'),
        'Titlu_Nr': context.get('titlu_nr'),
        'Titlu_Denumire': context.get('titlu_den'),
        'Capitol_Nr': context.get('capitol_nr'),
        'Capitol_Denumire': context.get('capitol_den'),
        'Sectiune_Nr': context.get('sectiune_nr'),
        'Sectiune_Denumire': context.get('sectiune_den'),
        'Subsectiune_Nr': context.get('subsectiune_nr'),
        'Subsectiune_Denumire': context.get('subsectiune_den'),
        'Art.1': article.get('nr'),
        'Art.2': 0,  # Pentru articole cu indici multiple
        'Articol_Label': article.get('label'),
        'Text_Articol': text_content if text_content else None
    }
    
    rows.append(row)

# Pentru compatibilitate cu codul existent
def parse_leg_printable_html(html_content: str) -> pd.DataFrame:
    """Wrapper pentru funcția principală"""
    return parse_html_legislative_structure(html_content)

# Funcții auxiliare pentru strategiile de parsing

def update_context_from_element(context: Dict[str, Any], element_type: Optional[str], text: str) -> None:
    """Actualizează contextul structural pe baza unui element"""
    if not element_type:
        return
        
    # Titluri
    if element_type == 'titlu_numar':
        # Extrage doar numărul titlului din S_TTL_TTL
        match = re.search(r'titlul\s+([IVXLCDM]+)', text, re.I)
        if match:
            context['titlu_nr'] = extract_roman_from_text(match.group(1))
    elif element_type == 'titlu_denumire':
        # Setează denumirea din S_TTL_DEN (fără număr)
        context['titlu_den'] = text.strip()
    
    # Capitole  
    elif element_type == 'capitol_titlu' or element_type == 'capitol_general':
        match = re.search(r'capitolul\s+([IVXLCDM]+)', text, re.I)
        if match:
            context['capitol_nr'] = extract_roman_from_text(match.group(1))
            # Nu setăm denumirea aici, va fi setată de S_CAP_DEN
            # Reset niveluri inferioare
            context['sectiune_nr'] = None
            context['sectiune_den'] = None
    
    elif element_type == 'capitol_denumire':
        # Setăm denumirea din S_CAP_DEN
        context['capitol_den'] = text.strip()
    
    # Secțiuni
    elif element_type == 'sectiune_titlu' or element_type == 'sectiune_general':
        # Extrage numărul din orice format: "Secțiunea 1", "Secțiunea a 2-a", etc.
        sec_nr = extract_number_from_text(text)
        if sec_nr:
            context['sectiune_nr'] = sec_nr
            # Nu setăm denumirea aici, va fi setată de S_SEC_DEN
    
    elif element_type == 'sectiune_denumire':
        # Setăm denumirea din S_SEC_DEN
        context['sectiune_den'] = text.strip()

def extract_article_from_element(element, context: Dict[str, Any], metadata: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """Extrage un articol dintr-un element HTML"""
    text = element.get_text(strip=True)
    
    # Identifică numărul articolului
    article_match = re.search(r'articol(ul)?\s+(\d+)(?:\^(\d+))?', text, re.I)
    if not article_match:
        return None
    
    article_num = int(article_match.group(2))
    article_idx = int(article_match.group(3)) if article_match.group(3) else 0
    
    # Găsește conținutul articolului (doar alineatele S_ALN)
    content = extract_article_content(element)
    
    return {
        'Mof_nr': metadata.get('mof_nr'),
        'Mof_Data': metadata.get('mof_data'),
        'Mof_An': None,
        'Emitent': None,
        'Tip_Act': metadata.get('tip_act'),
        'Nr': metadata.get('nr_act'),
        'Data_An': metadata.get('data_act'),
        'Denumire': metadata.get('denumire'),
        'Titlu_Nr': context.get('titlu_nr'),
        'Titlu_Denumire': context.get('titlu_den'),
        'Capitol_Nr': context.get('capitol_nr'),
        'Capitol_Denumire': context.get('capitol_den'),
        'Sectiune_Nr': context.get('sectiune_nr'),
        'Sectiune_Denumire': context.get('sectiune_den'),
        'Subsectiune_Nr': context.get('subsectiune_nr'),
        'Subsectiune_Denumire': context.get('subsectiune_den'),
        'Art.1': article_num,
        'Art.2': article_idx,
        'Articol_Label': text,  # Textul din S_ART_TTL (ex: "Articolul 1")
        'Text_Articol': content  # Doar alineatele S_ALN
    }

def extract_article_content(element) -> str:
    """
    Extrage conținutul unui articol din S_ART_BDY.
    Combină S_ALN_TTL (număr) cu S_ALN_BDY (text) pe același rând.
    Format: (1) Text alineat... \n (2) Text alineat...
    """
    # Caută S_ART_BDY (body-ul articolului) în siblings
    for sibling in element.find_next_siblings():
        classes = sibling.get('class', [])
        if not isinstance(classes, list):
            continue
        
        # Oprește-te dacă găsești un nou articol
        if 'S_ART_TTL' in classes:
            break
        
        # Găsit S_ART_BDY - procesează conținut
        if 'S_ART_BDY' in classes:
            content_lines = []
            
            # PRIORITATE 1: Verifică dacă există structură S_PAR + S_PCT (paragraf cu puncte)
            # Acest caz trebuie verificat ÎNAINTE de S_ALN pentru a evita confuzia
            # (S_ALN pot exista în interiorul S_PCT ca S_CIT)
            par_elements = sibling.find_all(class_=re.compile(r'S_PAR'), recursive=False)
            has_par_with_pct = False
            
            if par_elements:
                for par in par_elements:
                    # Verifică dacă acest S_PAR conține S_PCT
                    pct_children = par.find_all(class_=re.compile(r'S_PCT'))
                    if pct_children:
                        has_par_with_pct = True
                        break
            
            if has_par_with_pct:
                # CAZ SPECIAL: Articol cu paragraf introductiv + puncte enumerate
                # Exemplu: ORDIN 5/2023, Articolul 2
                
                for par in par_elements:
                    # Extrage textul introductiv (doar text direct, nu recursiv)
                    intro_texts = []
                    for child in par.children:
                        if isinstance(child, str):
                            text = child.strip()
                            if text:
                                intro_texts.append(text)
                    
                    if intro_texts:
                        intro = ' '.join(intro_texts)
                        content_lines.append(intro)
                    
                    # Extrage toate punctele (S_PCT) din acest paragraf
                    puncte = par.find_all(class_=re.compile(r'S_PCT'))
                    for pct in puncte:
                        ttl = pct.find(class_=re.compile(r'S_PCT_TTL'))
                        bdy = pct.find(class_=re.compile(r'S_PCT_BDY'))
                        
                        if ttl and bdy:
                            numero = ttl.get_text(strip=True)
                            text = bdy.get_text(strip=True)
                            if numero and text:
                                # Format: 1. Text punct...
                                if not numero.endswith('.'):
                                    numero += '.'
                                content_lines.append(f"{numero} {text}")
                
                return '\n'.join(content_lines) if content_lines else ''
            
            # PRIORITATE 2: Caută alineate S_ALN (structură normală)
            alineate = sibling.find_all(class_=re.compile(r'S_ALN'), recursive=False)
            
            if alineate:
                # Procesează fiecare alineat
                for aln in alineate:
                    # Caută S_ALN_TTL (numărul) și S_ALN_BDY (textul)
                    ttl = aln.find(class_=re.compile(r'S_ALN_TTL'))
                    bdy = aln.find(class_=re.compile(r'S_ALN_BDY'))
                    
                    if ttl and bdy:
                        # Combină pe același rând: (1) Text...
                        numero = ttl.get_text(strip=True)
                        text = bdy.get_text(strip=True)
                        if numero and text:
                            # Asigură spațiu după număr
                            if not numero.endswith(' '):
                                numero += ' '
                            content_lines.append(f"{numero}{text}")
                
                return '\n'.join(content_lines) if content_lines else ''
            
            # PRIORITATE 3: Fallback pentru paragraf simplu fără structură
            paragrafe = sibling.find_all(class_=re.compile(r'S_PAR'))
            if paragrafe:
                for par in paragrafe:
                    text = par.get_text(strip=True)
                    if text:
                        content_lines.append(text)
                return '\n'.join(content_lines) if content_lines else ''
            
            # PRIORITATE 4: Ultimul fallback - extrage tot textul
            text = sibling.get_text(separator='\n', strip=True)
            if text:
                return text
            
            return ''
    
    return ''

def extract_article_with_fuzzy_context(element, metadata: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """Extrage articol cu context fuzzy pentru strategia de rezervă"""
    text = element.get_text(strip=True)
    
    article_match = re.search(r'articol(ul)?\s+(\d+)', text, re.I)
    if not article_match:
        return None
        
    article_num = int(article_match.group(2))
    content = extract_article_content(element)
    
    return {
        **metadata,
        'Art.1': article_num,
        'Art.2': 0,
        'Articol_Label': text,
        'Text_Articol': content
    }

def extract_content_after_heading(heading) -> str:
    """Extrage conținutul după un heading"""
    content_parts = []
    
    for sibling in heading.find_next_siblings():
        if sibling.name in ['h1', 'h2', 'h3', 'h4', 'h5', 'h6']:
            break
            
        text = sibling.get_text(strip=True)
        if text:
            content_parts.append(text)
    
    return '\n'.join(content_parts)

def create_article_from_heading(heading, content: str, metadata: Dict[str, Any]) -> Dict[str, Any]:
    """Creează date articol din heading"""
    heading_text = heading.get_text(strip=True)
    
    article_match = re.search(r'articol(ul)?\s+(\d+)', heading_text, re.I)
    article_num = int(article_match.group(2)) if article_match else 0
    
    return {
        **metadata,
        'Art.1': article_num,
        'Art.2': 0,
        'Articol_Label': heading_text,
        'Text_Articol': content
    }

def extract_article_from_div(div, metadata: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """Extrage articol din div"""
    text = div.get_text(strip=True)
    
    article_match = re.search(r'articol(ul)?\s+(\d+)', text, re.I)
    if not article_match:
        return None
        
    article_num = int(article_match.group(2))
    
    return {
        **metadata,
        'Art.1': article_num,
        'Art.2': 0,
        'Articol_Label': text.split('\n')[0] if '\n' in text else text,
        'Text_Articol': text
    }

def create_article_from_text(article_label: str, content: str, metadata: Dict[str, Any]) -> Dict[str, Any]:
    """Creează date articol din text"""
    article_match = re.search(r'articol(ul)?\s+(\d+)', article_label, re.I)
    article_num = int(article_match.group(2)) if article_match else 0
    
    return {
        **metadata,
        'Art.1': article_num,
        'Art.2': 0,
        'Articol_Label': article_label,
        'Text_Articol': content
    }