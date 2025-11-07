#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Parser HTML pentru structura legislativă de pe legislatie.just.ro
Folosește clasele CSS specifice pentru extragere precisă
"""

import re
import pandas as pd
from typing import List, Dict, Optional, Any
from bs4 import BeautifulSoup
from config import TIPURI_ACTE_NORMATIVE


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
    """Strategia principală: folosește clasele CSS specifice"""
    rows = []
    metadata = extract_basic_metadata(soup)
    
    context = {
        'titlu_nr': None, 'titlu_den': None,
        'capitol_nr': None, 'capitol_den': None,
        'sectiune_nr': None, 'sectiune_den': None,
    }
    
    # Parcurge toate elementele în ordinea DOM
    for element in soup.find_all(class_=re.compile(r'^S_')):
        element_classes = element.get('class') or []
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
    """Calculează confidence score pentru rezultatele parsării"""
    if not results:
        return 0.0
    
    score = 0.0
    weights = {
        'has_articles': 0.5,
        'has_structure': 0.2,
        'has_content': 0.2,
        'has_metadata': 0.1
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


def classify_element(classes: List[str]) -> Optional[str]:
    """Clasifică elementul pe baza claselor CSS"""
    class_mapping = {
        'S_ART_TTL': 'articol_titlu',
        'S_ART': 'articol_general',
        'S_CAP_TTL': 'capitol_titlu',
        'S_CAP_DEN': 'capitol_denumire',
        'S_SEC_TTL': 'sectiune_titlu',
        'S_SEC_DEN': 'sectiune_denumire',
        'S_TTL_TTL': 'titlu_numar',
        'S_TTL_DEN': 'titlu_denumire',
    }
    
    for cls in classes:
        if cls in class_mapping:
            return class_mapping[cls]
    return None


def convert_month_to_number(luna: str) -> str:
    """Convertește numele lunii în număr"""
    months = {'ianuarie':'01','februarie':'02','martie':'03','aprilie':'04','mai':'05','iunie':'06',
              'iulie':'07','august':'08','septembrie':'09','octombrie':'10','noiembrie':'11','decembrie':'12'}
    return months.get(luna.lower(), '01')


def extract_basic_metadata(soup: BeautifulSoup) -> Dict[str, Any]:
    """Extrage metadata de bază din document"""
    metadata = {'Tip_Act': None, 'Nr': None, 'An': None, 'Data': None, 'Denumire': None}
    
    # Extrage tip act, număr și dată din S_DEN
    s_den = soup.find(class_='S_DEN')
    if s_den:
        den_text = s_den.get_text(strip=True)
        
        # Identifică tipul actului
        for tip in TIPURI_ACTE_NORMATIVE:
            if tip.lower() in den_text.lower():
                metadata['Tip_Act'] = tip
                break
        
        # Extrage numărul și data
        # Format comun: "LEGE nr. 123 din 30 aprilie 2024"
        match = re.search(r'nr\.?\s*(\d+)\s+din\s+(\d+)\s+(\w+)\s+(\d{4})', den_text, re.IGNORECASE)
        if match:
            metadata['Nr'] = int(match.group(1))
            zi = match.group(2)
            luna = convert_month_to_number(match.group(3))
            an = match.group(4)
            metadata['An'] = int(an)
            metadata['Data'] = f"{zi}/{luna}/{an}"
    
    # Extrage denumirea din S_HDR
    s_hdr = soup.find(class_='S_HDR')
    if s_hdr:
        metadata['Denumire'] = s_hdr.get_text(strip=True)
    
    return metadata


def update_context_from_element(context: Dict[str, Any], element_type: Optional[str], text: str) -> None:
    """Actualizează contextul structural pe baza tipului de element"""
    if element_type == 'titlu_numar':
        titlu_nr = extract_roman_from_text(text)
        context['titlu_nr'] = titlu_nr
        context['capitol_nr'] = None
        context['capitol_den'] = None
        context['sectiune_nr'] = None
        context['sectiune_den'] = None
        
    elif element_type == 'titlu_denumire':
        context['titlu_den'] = text.strip()
        
    elif element_type == 'capitol_titlu':
        cap_nr = extract_roman_from_text(text) or extract_number_from_text(text)
        context['capitol_nr'] = cap_nr
        context['sectiune_nr'] = None
        context['sectiune_den'] = None
        
    elif element_type == 'capitol_denumire':
        context['capitol_den'] = text.strip()
        
    elif element_type == 'sectiune_titlu':
        sec_nr = extract_number_from_text(text)
        context['sectiune_nr'] = sec_nr
        
    elif element_type == 'sectiune_denumire':
        context['sectiune_den'] = text.strip()


def extract_article_from_element(element, context: Dict[str, Any], metadata: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """Extrage datele articolului din element"""
    text_content = element.get_text(strip=True)
    art_nr = extract_number_from_text(text_content)
    
    if not art_nr:
        return None
    
    # Extrage conținutul articolului
    content = extract_article_content(element)
    
    return {
        'Articol_Nr': art_nr,
        'Articol_Label': text_content,
        'Text_Articol': content,
        'Titlu_Nr': context.get('titlu_nr'),
        'Titlu_Den': context.get('titlu_den'),
        'Capitol_Nr': context.get('capitol_nr'),
        'Capitol_Den': context.get('capitol_den'),
        'Sectiune_Nr': context.get('sectiune_nr'),
        'Sectiune_Den': context.get('sectiune_den'),
        'Tip_Act': metadata.get('Tip_Act'),
        'Nr': metadata.get('Nr'),
        'An': metadata.get('An'),
        'Data': metadata.get('Data'),
        'Denumire': metadata.get('Denumire'),
    }


def extract_article_content(element) -> str:
    """
    Extrage conținutul articolului din elementul S_ART_BDY care urmează după S_ART_TTL
    Procesează alineate, litere, puncte și paragrafe
    """
    content_parts = []
    
    # Găsește S_ART_BDY (corpul articolului)
    art_body = None
    for sibling in element.find_next_siblings():
        if 'S_ART_BDY' in sibling.get('class', []):
            art_body = sibling
            break
        # Oprește dacă găsești un nou articol
        if 'S_ART_TTL' in sibling.get('class', []):
            break
    
    if not art_body:
        return ''
    
    # Extrage structura din corpul articolului
    # Procesează alineate (S_ALN), litere (S_LIT), puncte (S_PCT) și paragrafe (S_PAR)
    for child in art_body.find_all(class_=re.compile(r'S_(ALN|LIT|PCT|PAR)'), recursive=False):
        classes = child.get('class', [])
        
        if 'S_ALN' in classes:
            # Alineat: extrage numărul și corpul
            aln_ttl = child.find(class_='S_ALN_TTL')
            aln_bdy = child.find(class_='S_ALN_BDY')
            if aln_ttl and aln_bdy:
                aln_num = aln_ttl.get_text(strip=True)
                aln_text = aln_bdy.get_text(strip=True)
                content_parts.append(f"{aln_num}...{aln_text}")
                
        elif 'S_LIT' in classes:
            # Literă: extrage litera și corpul
            lit_ttl = child.find(class_='S_LIT_TTL')
            lit_bdy = child.find(class_='S_LIT_BDY')
            if lit_ttl and lit_bdy:
                lit_letter = lit_ttl.get_text(strip=True)
                lit_text = lit_bdy.get_text(strip=True)
                content_parts.append(f"{lit_letter}...{lit_text}")
                
        elif 'S_PCT' in classes:
            # Punct: extrage numărul și corpul
            pct_ttl = child.find(class_='S_PCT_TTL')
            pct_bdy = child.find(class_='S_PCT_BDY')
            if pct_ttl and pct_bdy:
                pct_num = pct_ttl.get_text(strip=True)
                pct_text = pct_bdy.get_text(strip=True)
                content_parts.append(f"{pct_num} {pct_text}")
                
        elif 'S_PAR' in classes:
            # Paragraf simplu
            par_text = child.get_text(strip=True)
            if par_text:
                content_parts.append(par_text)
    
    # Dacă nu am găsit structură, ia tot textul
    if not content_parts:
        content_parts.append(art_body.get_text(strip=True))
    
    return '...'.join(content_parts)
