# De făcut / tech debt — SmartBill Intranet

Listă adunată pe parcurs, separată de `CHANGELOG.md` (care rămâne strict
istoric — "ce s-a făcut"). Aici e "ce a rămas de făcut", ca să nu se piardă
prin jurnal. La rezolvarea unui punct, se mută din listă în `CHANGELOG.md`,
la sesiunea în care s-a rezolvat efectiv (nu se șterge fără urmă).

## Producție (neînceput intenționat — se lucrează doar pe dev până la aprobare explicită de deploy)

Descoperit într-o revizie a proiectului, nu rezolvat încă:

1. `DJANGO_SETTINGS_MODULE` nu e setat nicăieri în afara hardcodării pe
   `config.settings.dev` din `config/wsgi.py` — pe server real ar rula tot
   cu setări de dev (`DEBUG=True`, `SECRET_KEY` hardcodat, `ALLOWED_HOSTS=["*"]`).
2. `config/settings/production.py` nu citește `SECRET_KEY`/`ALLOWED_HOSTS`
   din `.env` — trebuie completat.
3. `docker-compose.yml` rulează `manage.py runserver` (server de dev), nu
   `gunicorn` (deja în `requirements.txt`, neutilizat).
4. Media (`/media/...`) nu se servește deloc când `DEBUG=False` — lipsește
   un server care să preia asta (nginx sau echivalent).
5. `requirements.txt` fără versiuni fixate (`wagtail`, `psycopg`,
   `gunicorn`) — risc de breaking changes la rebuild.
6. Lipsesc setările HTTPS de producție (`SECURE_SSL_REDIRECT`,
   `SESSION_COOKIE_SECURE`, `CSRF_TRUSTED_ORIGINS`).
7. `WAGTAILADMIN_BASE_URL` trebuie pus pe domeniul real (altfel linkurile
   din notificările Wagtail duc spre `example.com`/`localhost`).
8. Notificările automate prin email pe workflow (submit/aprobare/respingere)
   sunt oprite intenționat (`home/wagtail_hooks.py`) — de reactivat când se
   rezolvă punctul 7, altfel linkurile din ele sunt greșite.
9. Furnizor real de email (SendGrid/Brevo/SES etc.) — discutat conceptual,
   nu configurat. Momentan merge pe Yahoo SMTP personal, doar pentru
   testare.

## Cod / funcționalitate (dev)

- **Izolare reală a imaginilor/documentelor per user** — momentan doar
  meniul "Images"/"Documents" e ascuns din admin pentru Angajați (curățenie
  de UI). Popup-ul de alegere a unei imagini/document, la adăugarea unui
  bloc în conținut, tot arată fișierele încărcate de colegi (permisiunea
  Wagtail de "choose" e pe Collection, nu per-uploader — confirmat empiric).
  Fix posibil, nativ Wagtail: o sub-Collection per user sub "Spatii
  personale" (ca la izolarea paginilor), cu `GroupCollectionPermission`
  scoped doar la userul respectiv. Aditiv, nu intră în conflict cu ce există.
- **Linkuri din RichText (paragraf) nu deschid în tab nou** — spre
  deosebire de blocurile dedicate document/link, care au deja
  `target="_blank"` din construcție. Editorul RichText de Wagtail nu are din
  cutie opțiune de "deschide în tab nou" pentru linkuri inline. Soluție de
  discutat (mic JS vs. procesare la randare) — ține cont de regula
  "zero JS" din `docs/RULES.md`.
- ✅ **Rezolvat** — Selector confuz la "Add child page" pe orice
  subsecțiune. `ErrorIndexPage`/`FAQIndexPage` aveau `parent_page_types`
  incluzând `home.MenuPage` (orice submeniu), fără `max_count` — efect:
  pe orice subsecțiune (chiar și "test1", "Proceduri" etc.) apărea un
  selector cu 3 opțiuni (Menu Page / Error Index Page / FAQ Index Page) în
  loc să creeze direct un submeniu. Fix (2026-07-11, native Wagtail, fără
  migrare — sunt atribute Python, nu câmpuri DB): `parent_page_types` pe
  `ErrorIndexPage`/`FAQIndexPage` restrâns la `["home.HomePage"]` (doar
  nivel principal) + `max_count = 1` pe ambele; scos `ErrorIndexPage`/
  `FAQIndexPage` din `subpage_types` al lui `MenuPage`. Verificat empiric
  (`creatable_subpage_models()`): Home → 3 opțiuni vizibile; orice
  submeniu (Suport, Proceduri) → doar `MenuPage`, fără selector. Teste
  4/4 OK.

## Training (fază ulterioară, menționată în cerințe, neîncepută)

Vezi `docs/requirements.md` — sistem de training tip Udemy, cu exerciții
trimise pe categorie, notificare trainer/manager la completare, review +
notă. De clarificat cu userul înainte de a începe (cine trimite exercițiile,
ce format, cum se notifică, ce nivel de "notă"). Legat de asta, și
clarificare GDPR/date sensibile pentru ce se stochează despre angajați noi.
