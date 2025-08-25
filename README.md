# Scraper Monitorul Oficial Partea I

Un script Python pentru extragerea metadatelor și PDF-urilor din Monitorul Oficial Partea I.

## Caracteristici

- Extrage metadate (titluri, numere, date, autorități emitente)
- Descarcă PDF-uri asociate documentelor
- Salvează datele într-un fișier CSV

## Cerințe

- Python 3.6+
- Biblioteci necesare:
  - requests
  - pandas
  - beautifulsoup4
  - playwright
  - lxml
  - tqdm

## Instalare

1. Clonează repository-ul
2. Instalează dependințele:
   `ash
   pip install -r requirements.txt
   playwright install
   `

## Utilizare

`ash
python scrape_mo_partea_i.py
`

Datele extrase vor fi salvate în mo_partea_i_last30.csv, iar PDF-urile în directorul mo_partea_i_pdfs/.
