# SmartBill Intranet — context pentru Claude Code

Proiect Django + Wagtail CMS, intranet intern SmartBill. Rulează în Docker
(`docker-compose.yml`: serviciu `web` cu `python manage.py runserver`, serviciu
`db` cu Postgres 16). Setări în `config/settings/` (`base.py` + `dev.py` +
`production.py`); local rulează pe `dev.py` (vezi `config/wsgi.py`).

## Unde găsești ce e de facut sau respectat sau de unde sa te informezi despre proiect:

- **`docs/requirements.md`** — cerințele originale complete ale userului
  (ce se dorește, faze, excepții). Sursa de adevăr pentru "ce".
- **`docs/RULES.md`** — reguli de lucru stabile, valabile pe termen lung
  (JS interzis, "Wagtail way", schimbări minime etc.). Sursa de adevăr
  pentru "cum".
- **`CHANGELOG.md`** — jurnal cronologic, pe sesiuni de lucru, strict
  istoric ("ce s-a făcut și ce s-a verificat"). Citește **ultimele 2-3
  secțiuni** înainte să începi treabă nouă.
- **`docs/TODO.md`** — tot ce a rămas de făcut (tech debt, găsit dar
  neexecutat, checklist producție). Citește-l la începutul oricărei sesiuni
  noi — orice găsești nou de tip "asta ar trebui reparat/discutat", adaugă-l
  aici, nu doar în răspunsul din chat.

## Cum continui pe altă mașină

1. `git pull`
2. `docker compose exec web python manage.py migrate` (aplică orice
   migrare nouă, inclusiv permisiuni/date create prin migrare)
3. Citește ultimele secțiuni din `CHANGELOG.md` — mai ales orice găsit
   marcat cu ⚠️ (probleme identificate dar nerezolvate încă)
4. La final de sesiune importantă, adaugă o secțiune nouă în
   `CHANGELOG.md` (nu rescrie ce există) — ce s-a schimbat, ce s-a
   verificat (programatic, nu doar presupus), ce rămâne deschis.
5. Dacă se stabilește o regulă nouă de lucru (nu doar o schimbare de cod),
   adaug-o și în `docs/RULES.md`.
