## 📊 Funcții Principale
- de ținut cont că nu mai e nevoie de câmpul issue (string) și că toate relațiile se vor ține în tabelele _issues (acte, articole, anexe, titluri, capitole, secțiuni)

## List articole, List acte, Get articol, Get act
- să extragă id-urile issues-urilor din tabelele corespunzătoare pe baza id-ului documentului

## Actualizările pe articol/acte/anexe etc nu mai conțin issue direct

## Funcții Issues
- List issues și  Get issue îți voi furniza endpointuri la mine de la care extragi aceste date
-  facem o funcții noi:

## Create Issues
## Update Issues
## Delete Issues

Parametri:
document_tip (poate fi string cu tipuri acceptate: acte, articole, anexe, titluri, capitole, sectiuni)
document_id bigint - id-ul documemtului
issue_id: int (daor pentru delete)

document_tip va functiona ca un router de selectie a tabelului

## create sql
INSERT INTO articole_issues SET articol_id = {document_id}, issue_id = {issue_id}, relevance_score = {relevance_score}, added_at = NOW();

## update sql
UPDATE articole_issues SET issue_id = {issue_id}, relevance_score = {relevance_score}, added_at = NOW() WHERE articol_id = {document_id};

## delete sql
DELETE FROM articole_issues WHERE articol_id = {document_id};
DELETE FROM articole_issues WHERE articol_id = {document_id} AND issue_id = {issue_id};
