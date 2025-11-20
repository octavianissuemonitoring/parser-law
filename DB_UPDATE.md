## 📊 Tabele Principale
`articole`

elmininăm
| `issue` | TEXT | NULL | **Eticheta Issue (din IM - analiză AI)** |
pentru că toatele datele ramân in tabelele de corespondență


rămân tabelele de issues:
`issues`
`acte_issues`
`articole_issues`
`anexe_issues`

propunere de adaugat pe viitor o tabele de corespondenta

`titluri`

| Coloană | Tip | Null | Descriere |
|---------|-----|------|-----------|
| `id` | INTEGER | PK | ID unic |
| `act_id` | INTEGER | FK → acte_legislative | Actul din care face parte |
| `titlu_nr` | INTEGER | NULL | Număr titlu (dacă face parte dintr-un titlu) |
| `titlu_denumire` | TEXT | NULL | Denumirea titlului |
| `ordine` | INTEGER | NULL | Ordinea în act (pentru sortare) |
| `created_at` | TIMESTAMP | DEFAULT now() | Data creării |
| `updated_at` | TIMESTAMP | DEFAULT now() | Data actualizării |

`capitole`

| Coloană | Tip | Null | Descriere |
|---------|-----|------|-----------|
| `id` | INTEGER | PK | ID unic |
| `act_id` | INTEGER | FK → acte_legislative | Actul din care face parte |
| `capitol_nr` | INTEGER | NULL | Număr capitol |
| `capitol_denumire` | TEXT | NULL | Denumirea capitolului |
| `ordine` | INTEGER | NULL | Ordinea în act (pentru sortare) |
| `created_at` | TIMESTAMP | DEFAULT now() | Data creării |
| `updated_at` | TIMESTAMP | DEFAULT now() | Data actualizării |

`sectiuni`

| Coloană | Tip | Null | Descriere |
|---------|-----|------|-----------|
| `id` | INTEGER | PK | ID unic |
| `act_id` | INTEGER | FK → acte_legislative | Actul din care face parte |
| `sectiune_denumire` | TEXT | NULL | Denumirea secțiunii |
| `subsectiune_nr` | INTEGER | NULL | Număr subsecțiune |
| `created_at` | TIMESTAMP | DEFAULT now() | Data creării |
| `updated_at` | TIMESTAMP | DEFAULT now() | Data actualizării |

+
`titluri_issues`

**Relație:** Many-to-Many între `titluri` și `issues`

| Coloană | Tip | Null | Descriere |
|---------|-----|------|-----------|
| `id` | INTEGER | PK | ID unic |
| `titlu_id` | INTEGER | FK → articole | PK Composite |
| `issue_id` | INTEGER | FK → issues | PK Composite |
| `relevance_score` | DOUBLE | NULL | Scor relevanță (0-1) |
| `added_at` | TIMESTAMP | DEFAULT now() | Când s-a adăugat |

`capitole_issues`
**Relație:** Many-to-Many între `capitole` și `issues`

| Coloană | Tip | Null | Descriere |
|---------|-----|------|-----------|
| `id` | INTEGER | PK | ID unic |
| `capitol_id` | INTEGER | FK → articole | PK Composite |
| `issue_id` | INTEGER | FK → issues | PK Composite |
| `relevance_score` | DOUBLE | NULL | Scor relevanță (0-1) |
| `added_at` | TIMESTAMP | DEFAULT now() | Când s-a adăugat |

`sectiuni_issues`
**Relație:** Many-to-Many între `sectiuni` și `issues`

| Coloană | Tip | Null | Descriere |
|---------|-----|------|-----------|
| `id` | INTEGER | PK | ID unic |
| `sectiune_id` | INTEGER | FK → articole | PK Composite |
| `issue_id` | INTEGER | FK → issues | PK Composite |
| `relevance_score` | DOUBLE | NULL | Scor relevanță (0-1) |
| `added_at` | TIMESTAMP | DEFAULT now() | Când s-a adăugat |


