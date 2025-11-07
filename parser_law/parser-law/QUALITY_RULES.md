# Reguli de Verificare Calitate

Acest document descrie regulile de verificare pentru fișierele CSV și Markdown generate de parser.

## Cum să Editezi Regulile

Regulile sunt definite în `quality_checker.py` în două metode:
- `_init_markdown_rules()` - reguli pentru Markdown
- `_init_csv_rules()` - reguli pentru CSV

### Structura unei Reguli

```python
"nume_regula": QualityRule(
    name="Nume Afișat",
    description="Descriere detaliată a cerinței",
    severity="error",  # "error", "warning", sau "info"
    enabled=True       # True = activă, False = dezactivată
)
```

### Severitate

- **error**: Probleme critice care trebuie rezolvate
- **warning**: Probleme care ar trebui rezolvate dar nu blochează
- **info**: Informații utile, non-critice

## Reguli Markdown (14 reguli)

### 1. Structură Obligatorie

| Regula | Severitate | Descriere |
|--------|-----------|-----------|
| `has_metadata_header` | error | Fișierul trebuie să înceapă cu metadata YAML (`---`) |
| `has_index` | error | Trebuie să existe secțiunea `## INDEX` |
| `has_articles` | error | Trebuie să existe secțiunea `## ARTICOLE` |

### 2. Formatare Alineate

| Regula | Severitate | Descriere |
|--------|-----------|-----------|
| `alineate_formatted` | warning | Alineatele (1), (2), (3) trebuie `**(1)**, **(2)**` |
| `no_unformatted_alineate` | warning | Nu trebuie alineate (1) fără bold |

**Exemplu corect:**
```markdown
**(1)** Text alineat primul
**(2)** Text alineat al doilea
```

**Exemplu greșit:**
```markdown
(1) Text alineat primul  ❌ (lipsește **)
```

### 3. Formatare Litere

| Regula | Severitate | Descriere |
|--------|-----------|-----------|
| `litere_formatted` | warning | Literele a), b), c) trebuie `**a)**, **b)**` |
| `litere_indented` | warning | Literele trebuie indentate cu 2 spații |

**Exemplu corect:**
```markdown
**(1)** Text alineat:

  **a)** litera a cu indentare
  **b)** litera b cu indentare
```

**Exemplu greșit:**
```markdown
**a)** litera fără indentare  ❌ (lipsesc cele 2 spații la început)
```

### 4. Referințe (NU trebuie formatate)

| Regula | Severitate | Descriere |
|--------|-----------|-----------|
| `references_not_formatted` | warning | `lit. a)`, `alin. (1)` NU trebuie bold |

**Exemplu corect:**
```markdown
conform prevederilor de la lit. a) și alin. (1)
```

**Exemplu greșit:**
```markdown
conform prevederilor de la **lit. a)** și **alin. (1)**  ❌
```

### 5. Linkuri INDEX

| Regula | Severitate | Descriere |
|--------|-----------|-----------|
| `index_links_valid` | warning | Linkuri în format `[Text](#anchor)` |
| `index_links_working` | error | Linkurile trebuie să ducă la articole existente |

### 6. Metadata

| Regula | Severitate | Descriere |
|--------|-----------|-----------|
| `metadata_complete` | warning | Câmpuri obligatorii: `tip_act`, `nr_act`, `data_act`, `total_articole` |

### 7. Context Ierarhic

| Regula | Severitate | Descriere |
|--------|-----------|-----------|
| `articles_have_context` | info | Fiecare articol trebuie să aibă context (Capitol/Secțiune) |

### 8. Normalizare Text

| Regula | Severitate | Descriere |
|--------|-----------|-----------|
| `no_extra_spaces` | warning | Nu trebuie spații multiple (3+) consecutive |
| `no_extra_newlines` | info | Nu trebuie mai mult de 2 newline-uri consecutive |

## Reguli CSV (8 reguli)

### 1. Structură Obligatorie

| Regula | Severitate | Descriere |
|--------|-----------|-----------|
| `has_required_columns` | error | Coloane obligatorii: `tip_element`, `text_articol`, `issue`, `explicatie` |

### 2. Date Complete

| Regula | Severitate | Descriere |
|--------|-----------|-----------|
| `no_empty_articles` | error | Toate articolele trebuie să aibă `text_articol` non-gol |
| `articles_have_numbers` | warning | Articolele trebuie să aibă `nr_articol` valid |

### 3. Coloane Editabile

| Regula | Severitate | Descriere |
|--------|-----------|-----------|
| `issue_column_exists` | warning | Coloana `issue` trebuie să existe |
| `explicatie_column_exists` | warning | Coloana `explicatie` trebuie să existe |

### 4. Consistență Date

| Regula | Severitate | Descriere |
|--------|-----------|-----------|
| `metadata_consistent` | warning | Metadata (`tip_act`, `nr_act`, `an_act`) consistentă între rânduri |

### 5. Ierarhie

| Regula | Severitate | Descriere |
|--------|-----------|-----------|
| `has_hierarchy` | info | Articolele trebuie să aibă ierarhie (`capitol`, `sectiune`) |

### 6. Numerotare

| Regula | Severitate | Descriere |
|--------|-----------|-----------|
| `article_numbers_sequential` | info | Numerele articolelor în ordine crescătoare |

## Cum să Adaugi o Regulă Nouă

### 1. Adaugă Regula în Dicționar

**Pentru Markdown**, în `_init_markdown_rules()`:

```python
"regula_mea_noua": QualityRule(
    name="Nume Regula",
    description="Ce verifică această regulă",
    severity="warning",
    enabled=True
)
```

**Pentru CSV**, în `_init_csv_rules()`:

```python
"regula_mea_noua": QualityRule(
    name="Nume Regula",
    description="Ce verifică această regulă",
    severity="error",
    enabled=True
)
```

### 2. Adaugă Metoda de Verificare

**Pentru Markdown**:

```python
def _check_md_regula_mea_noua(self, content: str) -> Tuple[bool, str]:
    """Descriere verificare"""
    # Logica de verificare
    if problema_gasita:
        return False, "Mesaj de eroare descriptiv"
    return True, "Mesaj de succes"
```

**Pentru CSV**:

```python
def _check_csv_regula_mea_noua(self, df: pd.DataFrame) -> Tuple[bool, str]:
    """Descriere verificare"""
    # Logica de verificare pe DataFrame
    if problema_gasita:
        return False, "Mesaj de eroare descriptiv"
    return True, "Mesaj de succes"
```

### 3. Exemplu Complet

```python
# 1. Adaugă în _init_markdown_rules()
"has_table_of_contents": QualityRule(
    name="Cuprins prezent",
    description="Verifică dacă există cuprins la început",
    severity="info",
    enabled=True
)

# 2. Adaugă metoda de verificare
def _check_md_has_table_of_contents(self, content: str) -> Tuple[bool, str]:
    """Verifică prezența cuprinsului"""
    if "## Cuprins" in content or "## TABLE OF CONTENTS" in content:
        return True, "Cuprins găsit"
    return False, "Lipsește cuprinsul"
```

## Dezactivarea unei Reguli

Pentru a dezactiva temporar o regulă fără să o ștergi:

```python
"regula_de_dezactivat": QualityRule(
    name="...",
    description="...",
    severity="warning",
    enabled=False  # ← Setează pe False
)
```

## Utilizare

### Verificare Director Complet

```bash
python quality_checker.py rezultate/
```

### Verificare Fișier Individual

```bash
python quality_checker.py rezultate/LEGE_123_2012.csv
python quality_checker.py rezultate/LEGE_123_2012.md
```

### În Cod Python

```python
from quality_checker import QualityChecker

checker = QualityChecker()

# Verifică un fișier
report = checker.check_markdown_file('rezultate/document.md')
checker.print_report(report)

# Verifică un director
results = checker.check_directory('rezultate/')
checker.print_summary(results)
```

## Interpretarea Rapoartelor

### Rata de Succes

- **90-100%**: Excelent, calitate foarte bună
- **70-89%**: Bun, câteva probleme minore
- **50-69%**: Acceptabil, necesită atenție
- **Sub 50%**: Problematic, necesită investigare

### Prioritizare

1. **Rezolvă ERORILE mai întâi** (severity="error")
2. **Apoi AVERTISMENTELE** (severity="warning")
3. **În final INFO** (severity="info") pentru îmbunătățiri

## Exemple de Rezultate

### Raport Individual

```
======================================================================
📋 Raport Calitate: LEGE_123_2012.md
📄 Tip: MARKDOWN
======================================================================

📊 Statistici:
   ✅ Verificări trecute: 12/14
   ❌ Verificări eșuate: 2/14
   🎯 Rata de succes: 85.7%

⚠️  AVERTISMENTE (2):
   ⚠️  [Alineate neformatate] Găsite 3 alineate neformatate
   ⚠️  [Linkuri INDEX valide] 2 linkuri cu format invalid
```

### Rezumat Director

```
📊 REZUMAT VERIFICARE CALITATE
======================================================================

📈 Total fișiere verificate: 14
✅ Total verificări trecute: 109
❌ Total verificări eșuate: 45
🎯 Rata de succes globală: 70.8%

⚠️  Fișiere cu ERORI (7):
   - LEGE_121_2024.csv
   - METODOLOGIE_2025.csv
```

## Best Practices

1. **Rulează verificatorul după fiecare parsare**
2. **Verifică întotdeauna rapoartele pentru erori critice**
3. **Adaugă reguli noi când descoperi probleme recurente**
4. **Documentează regulile noi în acest fișier**
5. **Testează regulile pe documente diverse**

## FAQ

**Q: Cum pot schimba severitatea unei reguli?**  
A: Modifică parametrul `severity` în definirea regulii (`"error"`, `"warning"`, sau `"info"`).

**Q: Pot avea reguli custom pentru anumite tipuri de documente?**  
A: Da! Adaugă logică condițională în metoda de verificare bazată pe metadata sau nume fișier.

**Q: Cum văd toate regulile disponibile?**  
A: Privește în metodele `_init_markdown_rules()` și `_init_csv_rules()` din `quality_checker.py`.

**Q: Pot exporta rapoartele în JSON/CSV?**  
A: Momentan nu, dar poți extinde clasa `QualityChecker` cu metode noi de export.
