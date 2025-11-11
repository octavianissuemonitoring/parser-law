# Phase 1 Implementation Guide - Quick Wins

**Timeline:** 1-2 zile  
**Risk:** LOW  
**Impact:** HIGH  
**Effort:** MIC

---

## 📋 Overview

Faza 1 conține 3 refactoring-uri prioritare care pot fi implementate rapid cu risc minim:

1. ✅ **Metadata Extractor** - Consolidare extractie metadata (2-3 ore)
2. ✅ **Query Builder** - Centralizare logică queries (3-4 ore)
3. ✅ **Endpoint Consolidation** - Merge endpoints redundante (2-3 ore)

**Total effort:** 7-10 ore (~1.5 zile)

---

## 🎯 Task 1: Metadata Extractor (Priority: HIGHEST)

### Problema Actuală

Metadata extraction este duplicată în 3 locuri:

```python
# html_parser.py - linia 182
def extract_basic_metadata(soup: BeautifulSoup) -> Dict[str, Any]:
    # ... 40 linii

# hybrid_parser.py - linia 150  
def _extract_html_metadata(self, soup: BeautifulSoup) -> Dict[str, Any]:
    # ... ACEEAȘI logică, 50 linii

# import_service.py - linia 220
async def _extract_metadata_from_html(self, html: str) -> dict:
    # ... iar ACEEAȘI logică
```

### Soluția: Modul Centralizat

**Pas 1:** Creează fișierul nou

<function_calls>
<invoke name="create_file">
<parameter name="content">#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Metadata Extractor - Single Source of Truth pentru extracție metadata din HTML legislativ
Centralizează logica de extracție din toate părțile sistemului
"""

import re
from typing import Optional, Dict, Any
from dataclasses import dataclass, field
from datetime import date, datetime
from bs4 import BeautifulSoup
from config import TIPURI_ACTE_NORMATIVE


@dataclass
class MOFData:
    """Metadata Monitorul Oficial"""
    nr: Optional[str] = None
    data: Optional[date] = None
    an: Optional[int] = None


@dataclass
class ActMetadata:
    """
    Metadata completă pentru un act normativ.
    Single Source of Truth pentru toate datele de identificare.
    """
    tip_act: Optional[str] = None
    nr_act: Optional[str] = None
    data_act: Optional[date] = None
    an_act: Optional[int] = None
    titlu_act: Optional[str] = None
    emitent_act: Optional[str] = None
    mof: MOFData = field(default_factory=MOFData)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convertește la dicționar pentru compatibilitate cu cod existent"""
        return {
            'tip_act': self.tip_act,
            'nr_act': self.nr_act,
            'data_act': self.data_act,
            'an_act': self.an_act,
            'titlu_act': self.titlu_act,
            'emitent_act': self.emitent_act,
            'mof_nr': self.mof.nr,
            'mof_data': self.mof.data,
            'mof_an': self.mof.an
        }


class MetadataExtractor:
    """
    Extractor centralizat de metadata din HTML legislativ.
    Înlocuiește toate implementările duplicate din:
    - html_parser.extract_basic_metadata()
    - hybrid_parser._extract_html_metadata()
    - import_service._extract_metadata_from_html()
    """
    
    # Patterns pentru detectare tipuri de acte și date
    PATTERNS = {
        'full': r'(LEGE|ORDONANȚ[AĂ]\s+DE\s+URGEN[TȚ][AĂ]|ORDONANȚ[AĂ]|HOT[AĂ]R[ÂÎ]RE|DECRET|ORDIN|REGULAMENT|NORM[AĂ]|INSTRUC[TȚ]IUNE|METODOLOGIE)\s+nr\.?\s*(\d+)\s+din\s+(\d{1,2})\s+(\w+)\s+(\d{4})',
        'short': r'(LEGE|ORDONANȚ[AĂ]\s+DE\s+URGEN[TȚ][AĂ]|ORDONANȚ[AĂ]|HOT[AĂ]R[ÂÎ]RE|DECRET|ORDIN|REGULAMENT|NORM[AĂ]|INSTRUC[TȚ]IUNE|METODOLOGIE)\s+nr\.?\s*(\d+)/(\d{4})',
        'no_number': r'(METODOLOGIE|REGULAMENT|NORM[AĂ]|INSTRUC[TȚ]IUNE)\s+din\s+(\d{1,2})\s+(\w+)\s+(\d{4})',
        'mof': r'MONITORUL\s+OFICIAL\s+(?:AL\s+ROM[AÂ]NIEI)?\s*[,\s]*PARTEA\s+I\s*[,\s]*nr\.?\s*(\d+)\s+din\s+(\d{1,2})\s+(\w+)\s+(\d{4})'
    }
    
    # Mapare luni românești → număr
    MONTHS = {
        'ianuarie': 1, 'februarie': 2, 'martie': 3, 'aprilie': 4,
        'mai': 5, 'iunie': 6, 'iulie': 7, 'august': 8,
        'septembrie': 9, 'octombrie': 10, 'noiembrie': 11, 'decembrie': 12
    }
    
    def extract(self, html: str) -> ActMetadata:
        """
        Extrage metadata completă din HTML.
        
        Args:
            html: Conținutul HTML al paginii legislație.just.ro
            
        Returns:
            ActMetadata cu toate câmpurile completate (unde sunt disponibile)
        """
        soup = BeautifulSoup(html, 'html.parser')
        
        return ActMetadata(
            tip_act=self._extract_tip_act(soup),
            nr_act=self._extract_nr_act(soup),
            data_act=self._extract_data_act(soup),
            an_act=self._extract_an_act(soup),
            titlu_act=self._extract_titlu(soup),
            emitent_act=self._extract_emitent(soup),
            mof=self._extract_mof(soup)
        )
    
    def _extract_tip_act(self, soup: BeautifulSoup) -> Optional[str]:
        """Extrage tipul actului (LEGE, OUG, ORDIN, etc.)"""
        s_den = soup.find(class_='S_DEN')
        if not s_den:
            return None
        
        text = s_den.get_text(strip=True).upper()
        
        # Verifică în ordinea priorității (mai specific → mai generic)
        for tip in TIPURI_ACTE_NORMATIVE:
            if tip.upper() in text:
                return tip
        
        # Fallback: încearcă cu patterns
        for pattern in self.PATTERNS.values():
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                return match.group(1).upper()
        
        return None
    
    def _extract_nr_act(self, soup: BeautifulSoup) -> Optional[str]:
        """Extrage numărul actului"""
        s_den = soup.find(class_='S_DEN')
        if not s_den:
            return None
        
        text = s_den.get_text(strip=True)
        
        # Încearcă pattern-uri în ordine
        # Pattern 1: "nr. 123 din 30 aprilie 2024"
        match = re.search(r'nr\.?\s*(\d+)\s+din', text, re.IGNORECASE)
        if match:
            return match.group(1)
        
        # Pattern 2: "nr. 123/2024"
        match = re.search(r'nr\.?\s*(\d+)/\d{4}', text, re.IGNORECASE)
        if match:
            return match.group(1)
        
        # Pattern 3: "nr. 123"
        match = re.search(r'nr\.?\s*(\d+)', text, re.IGNORECASE)
        if match:
            return match.group(1)
        
        return None
    
    def _extract_data_act(self, soup: BeautifulSoup) -> Optional[date]:
        """Extrage data actului (format date object)"""
        s_den = soup.find(class_='S_DEN')
        if not s_den:
            return None
        
        text = s_den.get_text(strip=True)
        
        # Pattern: "din 30 aprilie 2024"
        match = re.search(r'din\s+(\d{1,2})\s+(\w+)\s+(\d{4})', text, re.IGNORECASE)
        if match:
            zi = int(match.group(1))
            luna_str = match.group(2).lower()
            an = int(match.group(3))
            
            luna = self.MONTHS.get(luna_str)
            if luna:
                try:
                    return date(an, luna, zi)
                except ValueError:
                    pass
        
        return None
    
    def _extract_an_act(self, soup: BeautifulSoup) -> Optional[int]:
        """Extrage anul actului"""
        # Încearcă din data_act mai întâi
        data = self._extract_data_act(soup)
        if data:
            return data.year
        
        # Fallback: extrage din număr/an (ex: "123/2024")
        s_den = soup.find(class_='S_DEN')
        if s_den:
            text = s_den.get_text(strip=True)
            match = re.search(r'/(\d{4})', text)
            if match:
                return int(match.group(1))
        
        return None
    
    def _extract_titlu(self, soup: BeautifulSoup) -> Optional[str]:
        """Extrage titlul actului (denumirea completă)"""
        # Încearcă S_HDR (header principal)
        s_hdr = soup.find(class_='S_HDR')
        if s_hdr:
            return s_hdr.get_text(strip=True)
        
        # Fallback: S_DEN (după tipul actului)
        s_den = soup.find(class_='S_DEN')
        if s_den:
            text = s_den.get_text(strip=True)
            # Încearcă să extragă partea după "privind"
            match = re.search(r'privind\s+(.+)', text, re.IGNORECASE)
            if match:
                return match.group(1)
        
        return None
    
    def _extract_emitent(self, soup: BeautifulSoup) -> Optional[str]:
        """Extrage instituția emitentă"""
        # Căută în S_EMI (emitent) dacă există
        s_emi = soup.find(class_='S_EMI')
        if s_emi:
            return s_emi.get_text(strip=True)
        
        # Fallback: deduce din tip act
        # (ex: LEGE → Parlamentul României, ORDIN → Ministerul X)
        s_den = soup.find(class_='S_DEN')
        if s_den:
            text = s_den.get_text(strip=True)
            if 'PARLAMENTUL ROMÂNIEI' in text.upper():
                return 'Parlamentul României'
        
        return None
    
    def _extract_mof(self, soup: BeautifulSoup) -> MOFData:
        """Extrage informații Monitorul Oficial"""
        mof = MOFData()
        
        # Căută div cu clasa S_MOF sau text cu "MONITORUL OFICIAL"
        s_mof = soup.find(class_='S_MOF')
        if not s_mof:
            # Fallback: caută în tot textul
            s_mof = soup.find(string=re.compile(r'MONITORUL\s+OFICIAL', re.IGNORECASE))
            if s_mof:
                s_mof = s_mof.parent
        
        if s_mof:
            text = s_mof.get_text(strip=True)
            
            # Pattern: "MONITORUL OFICIAL nr. 123 din 30 aprilie 2024"
            match = re.search(self.PATTERNS['mof'], text, re.IGNORECASE)
            if match:
                mof.nr = match.group(1)
                zi = int(match.group(2))
                luna_str = match.group(3).lower()
                an = int(match.group(4))
                
                luna = self.MONTHS.get(luna_str)
                if luna:
                    try:
                        mof.data = date(an, luna, zi)
                        mof.an = an
                    except ValueError:
                        pass
        
        return mof
    
    @staticmethod
    def merge_metadata(base: ActMetadata, override: ActMetadata) -> ActMetadata:
        """
        Merge două obiecte ActMetadata (override are prioritate).
        Util pentru combinare CSV + MD metadata.
        """
        return ActMetadata(
            tip_act=override.tip_act or base.tip_act,
            nr_act=override.nr_act or base.nr_act,
            data_act=override.data_act or base.data_act,
            an_act=override.an_act or base.an_act,
            titlu_act=override.titlu_act or base.titlu_act,
            emitent_act=override.emitent_act or base.emitent_act,
            mof=MOFData(
                nr=override.mof.nr or base.mof.nr,
                data=override.mof.data or base.mof.data,
                an=override.mof.an or base.mof.an
            )
        )


# Instance globală pentru uz rapid
metadata_extractor = MetadataExtractor()


# Backward compatibility wrappers pentru cod existent
def extract_basic_metadata(soup: BeautifulSoup) -> Dict[str, Any]:
    """
    Wrapper pentru compatibilitate cu html_parser.py
    ⚠️ DEPRECATED: Folosește MetadataExtractor.extract() direct
    """
    html = str(soup)
    metadata = metadata_extractor.extract(html)
    return metadata.to_dict()


async def extract_metadata_from_html(html: str) -> dict:
    """
    Wrapper pentru compatibilitate cu import_service.py
    ⚠️ DEPRECATED: Folosește MetadataExtractor.extract() direct
    """
    metadata = metadata_extractor.extract(html)
    return metadata.to_dict()


if __name__ == '__main__':
    # Test cu HTML de exemplu
    test_html = """
    <div class="S_DEN">LEGE nr. 121 din 30 aprilie 2024</div>
    <div class="S_HDR">privind energia eoliană offshore</div>
    <div class="S_MOF">MONITORUL OFICIAL nr. 350 din 15 mai 2024</div>
    """
    
    extractor = MetadataExtractor()
    metadata = extractor.extract(test_html)
    
    print("Metadata extrasă:")
    print(f"  Tip Act: {metadata.tip_act}")
    print(f"  Nr Act: {metadata.nr_act}")
    print(f"  Data Act: {metadata.data_act}")
    print(f"  An Act: {metadata.an_act}")
    print(f"  Titlu: {metadata.titlu_act}")
    print(f"  MOF: {metadata.mof.nr} din {metadata.mof.data}")
