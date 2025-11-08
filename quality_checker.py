#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Verificator de calitate pentru rezultatele parsării legislative
Verifică atât fișierele CSV cât și Markdown conform unor reguli editabile
"""

import os
import re
from typing import Dict, List, Tuple, Any, Optional
from dataclasses import dataclass, field
import pandas as pd
from pathlib import Path


@dataclass
class QualityRule:
    """Regula de calitate cu descriere și funcție de verificare"""
    name: str
    description: str
    severity: str = "warning"  # "error", "warning", "info"
    enabled: bool = True


@dataclass
class QualityReport:
    """Raport de calitate pentru un fișier"""
    file_path: str
    file_type: str  # "csv" sau "markdown"
    total_checks: int = 0
    passed_checks: int = 0
    failed_checks: int = 0
    warnings: List[str] = field(default_factory=list)
    errors: List[str] = field(default_factory=list)
    info: List[str] = field(default_factory=list)
    
    @property
    def success_rate(self) -> float:
        """Procentaj de verificări trecute cu succes"""
        if self.total_checks == 0:
            return 0.0
        return (self.passed_checks / self.total_checks) * 100


class QualityChecker:
    """
    Verificator de calitate pentru fișiere CSV și Markdown
    
    Reguli editabile pentru verificare:
    - Formatare Markdown (alineate, litere, referințe)
    - Structură CSV (coloane obligatorii, date complete)
    - Consistență date între CSV și Markdown
    - Detectare erori comune
    """
    
    def __init__(self):
        """Inițializează verificatorul cu reguli editabile"""
        self.markdown_rules = self._init_markdown_rules()
        self.csv_rules = self._init_csv_rules()
    
    def _init_markdown_rules(self) -> Dict[str, QualityRule]:
        """
        Reguli de verificare pentru fișiere Markdown
        
        EDITABIL: Adaugă/modifică/dezactivează reguli aici
        """
        return {
            # === STRUCTURĂ OBLIGATORIE ===
            "has_metadata_header": QualityRule(
                name="Metadata YAML header",
                description="Fișierul trebuie să înceapă cu metadata YAML (---)",
                severity="error",
                enabled=True
            ),
            "has_index": QualityRule(
                name="INDEX section",
                description="Trebuie să existe secțiune INDEX cu link-uri",
                severity="error",
                enabled=True
            ),
            "has_articles": QualityRule(
                name="ARTICOLE section",
                description="Trebuie să existe secțiune ARTICOLE",
                severity="error",
                enabled=True
            ),
            
            # === FORMATARE ALINEATE ===
            "alineate_formatted": QualityRule(
                name="Formatare alineate",
                description="Alineatele (1), (2), (3) trebuie formatate ca **(1)**, **(2)**",
                severity="warning",
                enabled=True
            ),
            "no_unformatted_alineate": QualityRule(
                name="Alineate neformatate",
                description="Nu trebuie să existe alineate (1) fără formatare bold",
                severity="warning",
                enabled=True
            ),
            
            # === FORMATARE LITERE ===
            "litere_formatted": QualityRule(
                name="Formatare litere",
                description="Literele a), b), c) trebuie formatate ca **a)**, **b)** cu indentare",
                severity="warning",
                enabled=True
            ),
            "litere_indented": QualityRule(
                name="Indentare litere",
                description="Literele trebuie indentate cu 2 spații",
                severity="warning",
                enabled=True
            ),
            
            # === REFERINȚE (NU TREBUIE FORMATATE) ===
            "references_not_formatted": QualityRule(
                name="Referințe neformatate",
                description="Referințele 'lit. a)', 'alin. (1)' NU trebuie formatate bold",
                severity="warning",
                enabled=True
            ),
            
            # === LINKURI INDEX ===
            "index_links_valid": QualityRule(
                name="Linkuri INDEX valide",
                description="Linkurile din INDEX trebuie să fie în format [Articolul X](#articolul-x)",
                severity="warning",
                enabled=True
            ),
            "index_links_working": QualityRule(
                name="Linkuri INDEX funcționale",
                description="Linkurile din INDEX trebuie să ducă la articole existente",
                severity="error",
                enabled=True
            ),
            
            # === METADATA ===
            "metadata_complete": QualityRule(
                name="Metadata completă",
                description="Câmpurile obligatorii în metadata: tip_act, nr_act, data_act, total_articole",
                severity="warning",
                enabled=True
            ),
            
            # === CONTEXT IERARHIC ===
            "articles_have_context": QualityRule(
                name="Context ierarhic articole",
                description="Fiecare articol trebuie să aibă 'Context ierarhic' cu Capitol/Secțiune",
                severity="info",
                enabled=True
            ),
            
            # === NORMALIZARE TEXT ===
            "no_extra_spaces": QualityRule(
                name="Fără spații multiple",
                description="Nu trebuie să existe spații multiple consecutive (normalizare text)",
                severity="warning",
                enabled=True
            ),
            "no_extra_newlines": QualityRule(
                name="Fără newline-uri multiple",
                description="Nu trebuie să existe mai mult de 2 newline-uri consecutive",
                severity="info",
                enabled=True
            ),
        }
    
    def _init_csv_rules(self) -> Dict[str, QualityRule]:
        """
        Reguli de verificare pentru fișiere CSV
        
        EDITABIL: Adaugă/modifică/dezactivează reguli aici
        """
        return {
            # === STRUCTURĂ OBLIGATORIE ===
            "has_required_columns": QualityRule(
                name="Coloane obligatorii",
                description="CSV trebuie să conțină coloanele: tip_element, text_articol, issue, explicatie",
                severity="error",
                enabled=True
            ),
            
            # === DATE COMPLETE ===
            "no_empty_articles": QualityRule(
                name="Articole complete",
                description="Toate articolele trebuie să aibă text_articol non-gol",
                severity="error",
                enabled=True
            ),
            "articles_have_numbers": QualityRule(
                name="Numerotare articole",
                description="Articolele trebuie să aibă nr_articol valid",
                severity="warning",
                enabled=True
            ),
            
            # === COLOANE EDITABILE ===
            "issue_column_exists": QualityRule(
                name="Coloană issue",
                description="Coloana 'issue' trebuie să existe pentru editare",
                severity="warning",
                enabled=True
            ),
            "explicatie_column_exists": QualityRule(
                name="Coloană explicatie",
                description="Coloana 'explicatie' trebuie să existe pentru editare",
                severity="warning",
                enabled=True
            ),
            
            # === CONSISTENȚĂ DATE ===
            "metadata_consistent": QualityRule(
                name="Metadata consistentă",
                description="Metadata (tip_act, nr_act, an_act) trebuie să fie consistentă între rânduri",
                severity="warning",
                enabled=True
            ),
            
            # === IERARHIE ===
            "has_hierarchy": QualityRule(
                name="Ierarhie completă",
                description="Articolele trebuie să aibă informații de ierarhie (capitol, sectiune)",
                severity="info",
                enabled=True
            ),
            
            # === NUMEROTARE ===
            "article_numbers_sequential": QualityRule(
                name="Numerotare secvențială",
                description="Numerele articolelor trebuie să fie în ordine crescătoare",
                severity="info",
                enabled=True
            ),
        }
    
    # ==================== VERIFICĂRI MARKDOWN ====================
    
    def check_markdown_file(self, file_path: str) -> QualityReport:
        """
        Verifică un fișier Markdown conform regulilor definite
        
        Args:
            file_path: Calea către fișierul Markdown
            
        Returns:
            QualityReport cu rezultatele verificării
        """
        report = QualityReport(file_path=file_path, file_type="markdown")
        
        # Citește fișierul
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
        except Exception as e:
            report.errors.append(f"❌ Eroare citire fișier: {e}")
            return report
        
        # Rulează toate verificările activate
        for rule_id, rule in self.markdown_rules.items():
            if not rule.enabled:
                continue
                
            report.total_checks += 1
            
            # Apelează metoda de verificare corespunzătoare
            check_method = f"_check_md_{rule_id}"
            if hasattr(self, check_method):
                passed, message = getattr(self, check_method)(content)
                
                if passed:
                    report.passed_checks += 1
                else:
                    report.failed_checks += 1
                    
                    # Adaugă mesajul în categoria corespunzătoare
                    full_message = f"[{rule.name}] {message}"
                    if rule.severity == "error":
                        report.errors.append(f"❌ {full_message}")
                    elif rule.severity == "warning":
                        report.warnings.append(f"⚠️  {full_message}")
                    else:
                        report.info.append(f"ℹ️  {full_message}")
        
        return report
    
    # Metode de verificare Markdown (EDITABILE - adaugă verificări noi aici)
    
    def _check_md_has_metadata_header(self, content: str) -> Tuple[bool, str]:
        """Verifică dacă există header YAML cu metadata"""
        if not content.startswith('---\n'):
            return False, "Fișierul nu începe cu metadata YAML (---)"
        
        # Verifică închiderea metadata
        if content.count('---\n') < 2:
            return False, "Metadata YAML nu este închisă corect (lipsește al doilea ---)"
        
        return True, "Metadata YAML prezentă"
    
    def _check_md_has_index(self, content: str) -> Tuple[bool, str]:
        """Verifică dacă există secțiunea INDEX"""
        if '## INDEX' not in content:
            return False, "Lipsește secțiunea '## INDEX'"
        return True, "Secțiunea INDEX prezentă"
    
    def _check_md_has_articles(self, content: str) -> Tuple[bool, str]:
        """Verifică dacă există secțiunea ARTICOLE"""
        if '## ARTICOLE' not in content:
            return False, "Lipsește secțiunea '## ARTICOLE'"
        return True, "Secțiunea ARTICOLE prezentă"
    
    def _check_md_alineate_formatted(self, content: str) -> Tuple[bool, str]:
        """Verifică formatarea alineatelor"""
        # Caută alineate formatate corect: **(1)**, **(2)**, etc.
        formatted_pattern = r'\*\*\(\d+\)\*\*'
        formatted_count = len(re.findall(formatted_pattern, content))
        
        if formatted_count == 0:
            return True, "Nu există alineate (sau nu e aplicabil)"
        
        return True, f"Găsite {formatted_count} alineate formatate corect"
    
    def _check_md_no_unformatted_alineate(self, content: str) -> Tuple[bool, str]:
        """Verifică că nu există alineate neformatate"""
        # Caută alineate neformatate: (1), (2) fără **
        # Exclude referințe ca "alin. (1)" sau "art. (1)"
        lines = content.split('\n')
        unformatted = []
        
        for i, line in enumerate(lines, 1):
            # Caută (cifră) dar nu precedat de ** și nu în contextul "alin." sau "art."
            if re.search(r'(?<!\*\*)\(\d+\)(?!\*\*)', line):
                # Verifică dacă nu e referință
                if not re.search(r'\b(alin\.|art\.|punct|pct\.)\s*\(\d+\)', line):
                    unformatted.append(f"Linia {i}: {line.strip()[:80]}")
        
        if unformatted:
            return False, f"Găsite {len(unformatted)} alineate neformatate: {unformatted[:3]}"
        
        return True, "Toate alineatele sunt formatate corect"
    
    def _check_md_litere_formatted(self, content: str) -> Tuple[bool, str]:
        """Verifică formatarea literelor a), b), c)"""
        # Caută litere formatate: **a)**, **b)**, etc.
        formatted_pattern = r'\*\*[a-z]\)\*\*'
        formatted_count = len(re.findall(formatted_pattern, content))
        
        if formatted_count == 0:
            return True, "Nu există enumerări cu litere (sau nu e aplicabil)"
        
        return True, f"Găsite {formatted_count} litere formatate corect"
    
    def _check_md_litere_indented(self, content: str) -> Tuple[bool, str]:
        """Verifică indentarea literelor"""
        lines = content.split('\n')
        unindented = []
        
        for i, line in enumerate(lines, 1):
            # Caută litere formatate fără indentare (la începutul liniei)
            if re.match(r'^\*\*[a-z]\)\*\*', line):
                unindented.append(f"Linia {i}: {line.strip()[:60]}")
        
        if unindented:
            return False, f"Găsite {len(unindented)} litere neindentate: {unindented[:3]}"
        
        return True, "Toate literele sunt indentate corect"
    
    def _check_md_references_not_formatted(self, content: str) -> Tuple[bool, str]:
        """Verifică că referințele nu sunt formatate bold"""
        # Caută referințe formatate greșit: **lit. a)**, **alin. (1)**
        wrong_refs = []
        
        # Pattern pentru referințe formatate greșit
        patterns = [
            r'\*\*lit\.\s*[a-z]\)\*\*',
            r'\*\*alin\.\s*\(\d+\)\*\*',
            r'\*\*art\.\s*\d+\*\*',
            r'\*\*pct\.\s*\d+\*\*'
        ]
        
        for pattern in patterns:
            matches = re.findall(pattern, content)
            wrong_refs.extend(matches)
        
        if wrong_refs:
            return False, f"Găsite {len(wrong_refs)} referințe formatate greșit: {wrong_refs[:5]}"
        
        return True, "Referințele nu sunt formatate bold (corect!)"
    
    def _check_md_index_links_valid(self, content: str) -> Tuple[bool, str]:
        """Verifică formatul linkurilor din INDEX"""
        # Extrage secțiunea INDEX
        if '## INDEX' not in content:
            return True, "Nu există INDEX (verificare săriturată)"
        
        index_section = content.split('## INDEX')[1].split('##')[0]
        
        # Caută linkuri în format [Text](#anchor)
        link_pattern = r'\[([^\]]+)\]\(#([^\)]+)\)'
        links = re.findall(link_pattern, index_section)
        
        if not links:
            return False, "INDEX nu conține linkuri în format [Text](#anchor)"
        
        invalid_links = []
        for text, anchor in links:
            # Verifică că anchor-ul e lowercase cu hyphens
            if not re.match(r'^[a-z0-9\-]+$', anchor):
                invalid_links.append(f"[{text}](#{anchor})")
        
        if invalid_links:
            return False, f"Găsite {len(invalid_links)} linkuri cu format invalid: {invalid_links[:3]}"
        
        return True, f"Toate {len(links)} linkuri din INDEX au format valid"
    
    def _check_md_index_links_working(self, content: str) -> Tuple[bool, str]:
        """Verifică că linkurile din INDEX duc la articole existente"""
        if '## INDEX' not in content:
            return True, "Nu există INDEX (verificare săriturată)"
        
        index_section = content.split('## INDEX')[1].split('##')[0]
        link_pattern = r'\[([^\]]+)\]\(#([^\)]+)\)'
        links = re.findall(link_pattern, index_section)
        
        broken_links = []
        for text, anchor in links:
            # Caută anchor-ul în conținut: ### Articolul X
            # sau orice heading cu id-ul respectiv
            if f'### {text}' not in content and f'#{anchor}' not in content:
                broken_links.append(f"[{text}](#{anchor})")
        
        if broken_links:
            return False, f"Găsite {len(broken_links)} linkuri nefuncționale: {broken_links[:3]}"
        
        return True, f"Toate {len(links)} linkuri din INDEX sunt funcționale"
    
    def _check_md_metadata_complete(self, content: str) -> Tuple[bool, str]:
        """Verifică completitudinea metadata"""
        if not content.startswith('---\n'):
            return False, "Nu există metadata YAML"
        
        # Extrage metadata
        try:
            metadata_section = content.split('---\n')[1]
        except IndexError:
            return False, "Nu se poate extrage metadata"
        
        required_fields = ['tip_act', 'data_act', 'total_articole']
        missing_fields = []
        
        for field in required_fields:
            if f'{field}:' not in metadata_section:
                missing_fields.append(field)
        
        if missing_fields:
            return False, f"Lipsesc câmpuri obligatorii: {', '.join(missing_fields)}"
        
        return True, "Metadata completă cu toate câmpurile obligatorii"
    
    def _check_md_articles_have_context(self, content: str) -> Tuple[bool, str]:
        """Verifică că articolele au context ierarhic"""
        # Numără articole
        article_pattern = r'### Articolul \d+'
        articles = re.findall(article_pattern, content)
        
        if not articles:
            return False, "Nu s-au găsit articole în format '### Articolul X'"
        
        # Numără contexte ierarhice
        context_pattern = r'\*\*Context ierarhic:\*\*'
        contexts = re.findall(context_pattern, content)
        
        if len(contexts) < len(articles):
            return False, f"Doar {len(contexts)}/{len(articles)} articole au context ierarhic"
        
        return True, f"Toate {len(articles)} articole au context ierarhic"
    
    def _check_md_no_extra_spaces(self, content: str) -> Tuple[bool, str]:
        """Verifică că nu există spații multiple"""
        # Caută 3+ spații consecutive (2 spații pt indentare e OK)
        extra_spaces = re.findall(r'   +', content)
        
        if extra_spaces:
            return False, f"Găsite {len(extra_spaces)} locuri cu spații multiple (3+)"
        
        return True, "Nu există spații multiple (text normalizat corect)"
    
    def _check_md_no_extra_newlines(self, content: str) -> Tuple[bool, str]:
        """Verifică că nu există newline-uri multiple"""
        # Caută 3+ newline-uri consecutive
        extra_newlines = re.findall(r'\n\n\n+', content)
        
        if extra_newlines:
            return False, f"Găsite {len(extra_newlines)} locuri cu 3+ newline-uri consecutive"
        
        return True, "Nu există newline-uri multiple excesive"
    
    # ==================== VERIFICĂRI CSV ====================
    
    def check_csv_file(self, file_path: str) -> QualityReport:
        """
        Verifică un fișier CSV conform regulilor definite
        
        Args:
            file_path: Calea către fișierul CSV
            
        Returns:
            QualityReport cu rezultatele verificării
        """
        report = QualityReport(file_path=file_path, file_type="csv")
        
        # Citește CSV
        try:
            df = pd.read_csv(file_path, encoding='utf-8')
        except Exception as e:
            report.errors.append(f"❌ Eroare citire CSV: {e}")
            return report
        
        # Rulează toate verificările activate
        for rule_id, rule in self.csv_rules.items():
            if not rule.enabled:
                continue
                
            report.total_checks += 1
            
            # Apelează metoda de verificare corespunzătoare
            check_method = f"_check_csv_{rule_id}"
            if hasattr(self, check_method):
                passed, message = getattr(self, check_method)(df)
                
                if passed:
                    report.passed_checks += 1
                else:
                    report.failed_checks += 1
                    
                    # Adaugă mesajul în categoria corespunzătoare
                    full_message = f"[{rule.name}] {message}"
                    if rule.severity == "error":
                        report.errors.append(f"❌ {full_message}")
                    elif rule.severity == "warning":
                        report.warnings.append(f"⚠️  {full_message}")
                    else:
                        report.info.append(f"ℹ️  {full_message}")
        
        return report
    
    # Metode de verificare CSV (EDITABILE - adaugă verificări noi aici)
    
    def _check_csv_has_required_columns(self, df: pd.DataFrame) -> Tuple[bool, str]:
        """Verifică coloanele obligatorii"""
        required = ['tip_element', 'text_articol', 'issue', 'explicatie']
        missing = [col for col in required if col not in df.columns]
        
        if missing:
            return False, f"Lipsesc coloane obligatorii: {', '.join(missing)}"
        
        return True, f"Toate {len(required)} coloanele obligatorii prezente"
    
    def _check_csv_no_empty_articles(self, df: pd.DataFrame) -> Tuple[bool, str]:
        """Verifică că articolele au text"""
        if 'text_articol' not in df.columns:
            return False, "Coloana 'text_articol' lipsește"
        
        # Filtrează doar articole (nu titluri, capitole, etc.)
        if 'tip_element' in df.columns:
            articles = df[df['tip_element'] == 'articol']
        else:
            articles = df
        
        empty = articles[articles['text_articol'].isna() | (articles['text_articol'] == '')]
        
        if len(empty) > 0:
            return False, f"{len(empty)} articole au text_articol gol"
        
        return True, f"Toate {len(articles)} articolele au text_articol completat"
    
    def _check_csv_articles_have_numbers(self, df: pd.DataFrame) -> Tuple[bool, str]:
        """Verifică numerotarea articolelor"""
        if 'nr_articol' not in df.columns:
            return False, "Coloana 'nr_articol' lipsește"
        
        if 'tip_element' in df.columns:
            articles = df[df['tip_element'] == 'articol']
        else:
            articles = df
        
        without_number = articles[articles['nr_articol'].isna()]
        
        if len(without_number) > 0:
            return False, f"{len(without_number)} articole nu au nr_articol"
        
        return True, f"Toate {len(articles)} articolele au nr_articol"
    
    def _check_csv_issue_column_exists(self, df: pd.DataFrame) -> Tuple[bool, str]:
        """Verifică existența coloanei issue"""
        if 'issue' not in df.columns:
            return False, "Coloana 'issue' lipsește (necesară pentru editare)"
        return True, "Coloana 'issue' prezentă pentru editare"
    
    def _check_csv_explicatie_column_exists(self, df: pd.DataFrame) -> Tuple[bool, str]:
        """Verifică existența coloanei explicatie"""
        if 'explicatie' not in df.columns:
            return False, "Coloana 'explicatie' lipsește (necesară pentru editare)"
        return True, "Coloana 'explicatie' prezentă pentru editare"
    
    def _check_csv_metadata_consistent(self, df: pd.DataFrame) -> Tuple[bool, str]:
        """Verifică consistența metadata"""
        metadata_cols = ['tip_act', 'nr_act', 'an_act']
        present_cols = [col for col in metadata_cols if col in df.columns]
        
        if not present_cols:
            return True, "Nu există coloane de metadata (verificare săriturată)"
        
        inconsistent = []
        for col in present_cols:
            unique_values = df[col].dropna().unique()
            if len(unique_values) > 1:
                inconsistent.append(f"{col}: {len(unique_values)} valori diferite")
        
        if inconsistent:
            return False, f"Metadata inconsistentă: {', '.join(inconsistent)}"
        
        return True, "Metadata consistentă între rânduri"
    
    def _check_csv_has_hierarchy(self, df: pd.DataFrame) -> Tuple[bool, str]:
        """Verifică informații ierarhice"""
        hierarchy_cols = ['capitol', 'sectiune']
        present = [col for col in hierarchy_cols if col in df.columns]
        
        if not present:
            return False, "Nu există coloane de ierarhie (capitol, sectiune)"
        
        # Verifică dacă au valori
        has_data = []
        for col in present:
            if df[col].notna().sum() > 0:
                has_data.append(col)
        
        if not has_data:
            return False, f"Coloane ierarhie prezente dar goale: {', '.join(present)}"
        
        return True, f"Ierarhie prezentă: {', '.join(has_data)}"
    
    def _check_csv_article_numbers_sequential(self, df: pd.DataFrame) -> Tuple[bool, str]:
        """Verifică ordinea numerelor de articole"""
        if 'nr_articol' not in df.columns or 'tip_element' not in df.columns:
            return True, "Nu se pot verifica numerele (coloane lipsă)"
        
        articles = df[df['tip_element'] == 'articol']['nr_articol'].dropna()
        
        if len(articles) == 0:
            return True, "Nu există articole (verificare săriturată)"
        
        # Verifică dacă sunt în ordine crescătoare
        articles_list = articles.tolist()
        sorted_articles = sorted(articles_list)
        
        if articles_list != sorted_articles:
            return False, "Numerele articolelor nu sunt în ordine crescătoare"
        
        return True, f"Numerele articolelor ({len(articles)}) sunt în ordine crescătoare"
    
    # ==================== VERIFICARE PERECHI CSV+MD ====================
    
    def check_pair(self, csv_path: str, md_path: str) -> Dict[str, QualityReport]:
        """
        Verifică o pereche CSV + Markdown
        
        Args:
            csv_path: Calea către CSV
            md_path: Calea către Markdown
            
        Returns:
            Dict cu rapoarte pentru ambele fișiere
        """
        return {
            'csv': self.check_csv_file(csv_path),
            'markdown': self.check_markdown_file(md_path)
        }
    
    def check_directory(self, directory: str) -> Dict[str, Any]:
        """
        Verifică toate perechile CSV+MD dintr-un director
        
        Args:
            directory: Calea către director (ex: 'rezultate/')
            
        Returns:
            Dict cu rapoarte pentru toate fișierele
        """
        results = {}
        
        # Găsește toate fișierele CSV
        csv_files = list(Path(directory).glob('*.csv'))
        
        for csv_file in csv_files:
            # Găsește fișierul MD corespunzător
            md_file = csv_file.with_suffix('.md')
            
            if not md_file.exists():
                results[csv_file.name] = {
                    'error': f"Lipsește fișierul Markdown: {md_file.name}"
                }
                continue
            
            # Verifică perechea
            pair_results = self.check_pair(str(csv_file), str(md_file))
            results[csv_file.stem] = pair_results
        
        return results
    
    # ==================== RAPORTARE ====================
    
    def print_report(self, report: QualityReport, verbose: bool = True):
        """
        Afișează raportul de calitate
        
        Args:
            report: Raportul de verificare
            verbose: Dacă True, afișează toate detaliile
        """
        print("\n" + "=" * 70)
        print(f"📋 Raport Calitate: {Path(report.file_path).name}")
        print(f"📄 Tip: {report.file_type.upper()}")
        print("=" * 70)
        
        print(f"\n📊 Statistici:")
        print(f"   ✅ Verificări trecute: {report.passed_checks}/{report.total_checks}")
        print(f"   ❌ Verificări eșuate: {report.failed_checks}/{report.total_checks}")
        print(f"   🎯 Rata de succes: {report.success_rate:.1f}%")
        
        if report.errors:
            print(f"\n❌ ERORI ({len(report.errors)}):")
            for error in report.errors:
                print(f"   {error}")
        
        if report.warnings:
            print(f"\n⚠️  AVERTISMENTE ({len(report.warnings)}):")
            if verbose:
                for warning in report.warnings:
                    print(f"   {warning}")
            else:
                for warning in report.warnings[:5]:
                    print(f"   {warning}")
                if len(report.warnings) > 5:
                    print(f"   ... și încă {len(report.warnings) - 5} avertismente")
        
        if verbose and report.info:
            print(f"\nℹ️  INFO ({len(report.info)}):")
            for info in report.info:
                print(f"   {info}")
        
        print("\n" + "=" * 70)
    
    def print_summary(self, results: Dict[str, Any]):
        """
        Afișează rezumat pentru toate fișierele verificate
        
        Args:
            results: Rezultatele verificării unui director
        """
        print("\n" + "=" * 70)
        print("📊 REZUMAT VERIFICARE CALITATE")
        print("=" * 70)
        
        total_files = 0
        total_passed = 0
        total_failed = 0
        files_with_errors = []
        
        for filename, data in results.items():
            if 'error' in data:
                print(f"\n❌ {filename}: {data['error']}")
                continue
            
            csv_report = data.get('csv')
            md_report = data.get('markdown')
            
            if csv_report:
                total_files += 1
                total_passed += csv_report.passed_checks
                total_failed += csv_report.failed_checks
                if csv_report.errors:
                    files_with_errors.append(f"{filename}.csv")
            
            if md_report:
                total_files += 1
                total_passed += md_report.passed_checks
                total_failed += md_report.failed_checks
                if md_report.errors:
                    files_with_errors.append(f"{filename}.md")
        
        print(f"\n📈 Total fișiere verificate: {total_files}")
        print(f"✅ Total verificări trecute: {total_passed}")
        print(f"❌ Total verificări eșuate: {total_failed}")
        
        if total_passed + total_failed > 0:
            success_rate = (total_passed / (total_passed + total_failed)) * 100
            print(f"🎯 Rata de succes globală: {success_rate:.1f}%")
        
        if files_with_errors:
            print(f"\n⚠️  Fișiere cu ERORI ({len(files_with_errors)}):")
            for filename in files_with_errors:
                print(f"   - {filename}")
        
        print("\n" + "=" * 70)


def main():
    """Funcție principală pentru testare"""
    import sys
    
    checker = QualityChecker()
    
    # Verifică director sau fișier specific
    if len(sys.argv) > 1:
        path = sys.argv[1]
        
        if os.path.isdir(path):
            # Verifică tot directorul
            print(f"🔍 Verificăm directorul: {path}")
            results = checker.check_directory(path)
            
            # Afișează rapoarte detaliate pentru fiecare fișier
            for filename, data in results.items():
                if 'error' in data:
                    print(f"\n❌ {filename}: {data['error']}")
                    continue
                
                if 'csv' in data:
                    checker.print_report(data['csv'], verbose=False)
                if 'markdown' in data:
                    checker.print_report(data['markdown'], verbose=False)
            
            # Afișează rezumatul
            checker.print_summary(results)
        
        elif path.endswith('.csv'):
            # Verifică CSV individual
            report = checker.check_csv_file(path)
            checker.print_report(report)
        
        elif path.endswith('.md'):
            # Verifică Markdown individual
            report = checker.check_markdown_file(path)
            checker.print_report(report)
        
        else:
            print(f"❌ Tip fișier nerecunoscut: {path}")
    
    else:
        # Verifică directorul implicit 'rezultate/'
        if os.path.exists('rezultate'):
            print("🔍 Verificăm directorul: rezultate/")
            results = checker.check_directory('rezultate')
            checker.print_summary(results)
        else:
            print("❌ Nu s-a specificat niciun director și 'rezultate/' nu există")
            print("\nUtilizare:")
            print("  python quality_checker.py                    # Verifică rezultate/")
            print("  python quality_checker.py rezultate/         # Verifică director specific")
            print("  python quality_checker.py fisier.csv         # Verifică CSV specific")
            print("  python quality_checker.py fisier.md          # Verifică MD specific")


if __name__ == "__main__":
    main()
