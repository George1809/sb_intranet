# SmartBill Intranet — context pentru Claude Code

Proiect Django + Wagtail CMS, intranet intern SmartBill. Rulează în Docker
(`docker-compose.yml`: serviciu `web` cu `python manage.py runserver`, serviciu
`db` cu Postgres 16). Setări în `config/settings/` (`base.py` + `dev.py` +
`production.py`); local ruleaza pe `dev.py` (vezi `config/wsgi.py`).

Acest fișier e gândit ca jurnal continuu — la fiecare sesiune de lucru
importantă, adaugă o secțiune nouă dedesubt (nu rescrie istoricul), ca oricine
(om sau Claude, pe orice mașină) să poată vedea rapid ce s-a făcut, ce s-a
verificat și care e concluzia. Se sincronizează prin git normal (push/pull)
între mașini.

## Reguli de lucru stabilite cu userul (valabile pe termen lung)

- **Zero JS** pe partea de site — doar CSS + Django/Wagtail template-uri.
- **Cât mai "Wagtail way"** — preferă funcții native Wagtail (Collections,
  Groups/permissions, Workflows, hooks) în locul codului custom. Cod custom
  doar acolo unde Wagtail chiar nu acoperă nativ, și cât mai izolat/minim.
  Fii transparent explicit când o soluție NU e nativă și de ce.
- Schimbări **minime, stabile, reversibile** — nu adăuga abstractizări sau
  funcționalități neprezente în cerință.
- Modelele de Document/Imagine Wagtail rămân cele **implicite** — s-a decis
  explicit împotriva înlocuirii lor cu modele custom (discutat, respins în
  favoarea Collections native, ca sa nu creeze datorie tehnica la upgrade-uri
  viitoare de Wagtail).
- Producția e **amânată** intenționat — se lucrează doar pe dev până la
  aprobare explicită de deploy. Nu activa/configura infrastructură de
  producție fără cerere clară.

## Sesiune 2026-07-10 (Windows, dev local via Docker)

### 1. Font + layout (CSS, zero Wagtail)
- Randare "bolduită"/urâtă pe alt monitor -> cauza: fontul "Inter" era cerut
  în CSS dar nu era încărcat nicăieri (fallback pe Segoe UI, faux-bold la
  greutăți 800/900). Rezolvat prin self-host Inter Variable (woff2, subset
  latin + latin-ext pt. diacritice RO) în `config/static/fonts/` +
  `@font-face` în `config/static/css/sb.css`. Sursa: pachetul open-source
  `@fontsource-variable/inter` (licență SIL OFL, inclusă lângă fonturi).
- Conținut tăiat pe laptop cu ecran mic (1920x1200 @ 125% scalare Windows =
  ~960px înălțime logică, mai puțin cu chrome-ul browserului) -> adăugat un
  `@media (max-height: 900px)` în `sb.css` care compactează spațierile
  hero-ului/dashboard-ului doar sub acel prag. Nu afectează monitoare înalte.
- **Verificat**: confirmat vizual de user pe ambele ecrane (acasă + laptop).

### 2. Migrații lipsă (context, nu schimbare de cod)
- Eroare `relation ... does not exist` pe laptopul Windows -> cauza: DB
  Postgres e într-un volum Docker local per mașină, nu se sincronizează prin
  git; migrațiile trebuie rulate manual (`docker compose exec web python
  manage.py migrate`) după fiecare `git pull` care aduce migrări noi. Userul
  a rulat manual, rezolvat.

### 3. Organizare media — Collections native (zero cod)
- S-a decis împotriva unei structuri fizice de foldere pe disc (ar fi
  necesitat modele custom de Document/Imagine — respins, vezi regulile de
  mai sus). În loc, s-a creat arborele de **Collections** Wagtail (nativ,
  vizibil doar în admin, nu pe disc), oglindind structura de meniu:
  ```
  Release Notes, Training, Tools, Quick links,
  Suport (-> Proceduri, Case de marcat, Flags),
  Vanzari, Conta, Reseller, Cazuri & intrebari
  ```
  Creat printr-un script one-off rulat direct în shell (NU cod persistent —
  echivalent cu a le crea manual din admin, doar automatizat).

### 4. Model de permisiuni pe 3 niveluri
Cerință: ~30 useri, 5-6 cu drepturi depline, restul limitați la spațiul
personal + FAQ/Erori (cu aprobare).

- **Administrator** (bifa "Superuser" la user) — cei 5-6 cu drepturi depline.
  Nu se pune și în vreun grup, superuser-ul acoperă deja tot.
- **Moderators** (grup implicit Wagtail, refolosit ca atare, nemodificat) —
  pentru un nivel intermediar opțional: editare+publicare peste tot
  (meniuri/FAQ/Erori), dar FĂRĂ acces de administrare (useri/settings) și,
  important, **cu izolare pe spațiul personal** (vezi punctul 5 — hook-urile
  sunt generice, se aplică oricărui non-superuser, nu doar grupului
  "Angajati"). E și grupul care aprobă workflow-ul de FAQ/Erori.
- **Angajati** (grup nou, creat prin migrare `home/migrations/
  0012_grup_angajati_permisiuni.py`) — acces limitat:
  - Poate crea/edita dar NU publica pe FAQ ("Intrebari") și Erori ("Erori")
    -> merge automat la workflow de aprobare ("Aprobare Angajati"), aprobat
    de grupul Moderators (fără notificări email — dezactivate global, vezi
    `wagtail_hooks.py`, rămân doar la resetare/schimbare parolă).
  - Poate crea/edita ȘI publica direct propriul Spațiu personal (nu al
    colegilor — vezi hook-urile de izolare).
  - Poate încărca imagini/documente (inclusiv video ca fișier) DOAR în
    Collections dedicate: "Cazuri & intrebari" (doar imagini) și "Spatii
    personale" (imagini + documente/video). Zero acces la restul bibliotecii
    de documente/imagini, zero acces la meniuri (Suport/Vanzari/etc).
  - Migrația a creat și paginile `FAQIndexPage`/`ErrorIndexPage` sub "Cazuri
    & intrebari" (nu existau deloc înainte — descoperire făcută în timpul
    lucrului, nu presupunere).
- **Editors** (grup implicit Wagtail) — rămâne complet neutilizat, gol,
  intenționat. Editează/adaugă peste tot dar nu publică — nu se potrivește
  modelului dorit, s-a decis să nu fie folosit.

### 5. Izolare spațiu personal — singura bucată de cod custom real
Wagtail NU are nativ conceptul "acces pe un subarbore comun, dar fiecare
user vede doar rândul lui" (permisiunile sunt pe grup+subarbore întreg).
Adăugate 2 hook-uri în `home/wagtail_hooks.py` (mecanism oficial Wagtail,
nu un hack):
- `construct_explorer_page_queryset` — filtrează listarea din admin: un
  non-superuser vede doar propriul `PersonalSpacePage`, niciodată ale
  colegilor. Superuserii văd tot. Totodată, la prima navigare aici, creează
  automat pagina personală a userului dacă nu exista încă (altfel cineva
  care intră direct în admin, fără să fi vizitat `/spatiul-meu/` întâi, nu
  avea nicio pagină de editat — bug descoperit și reparat în sesiune).
- `before_edit_page` — a doua linie de apărare: blochează (403) accesul
  direct la editarea spațiului altcuiva, chiar dacă cineva ghicește URL-ul.

Important: aceste hook-uri sunt **generice**, se aplică oricărui
non-superuser, indiferent de grup — de-aia funcționează la fel de bine și
pentru "Angajati", și pentru "Moderators" (verificat separat pentru ambele).

### 6. `PersonalSpacePage.is_creatable = False`
Crash (`ValidationError: owner_user ... nu poate fi nul`) când cineva încerca
"Add child page" manual pe Spații personale — pagina nu e gândită să fie
creată așa (se creează automat, 1/user, prin `get_or_create_for_user()`, iar
`owner_user` nici nu apare în formular). Fix cu un rând (`is_creatable =
False` în `home/models.py`) — Wagtail ascunde butonul ȘI blochează server-side
(`PermissionDenied`) accesul direct pe URL, confirmat din sursa Wagtail
instalată (7.4.2), nu presupus.

### 7. Scurgere de intimitate în căutarea globală
Căutarea globală (`search/views.py`) folosea `Page.objects.live().public()`,
care includea și `PersonalSpacePage`/`PersonalSpaceIndexPage` — deși
"private" în admin, apăreau în căutarea de pe site pentru orice user care
căuta un cuvânt din titlu (ex. un nume). Descoperit prin testare directă (nu
presupunere — prima ipoteză, că era deja exclus, s-a dovedit greșită).
Reparat cu `.not_type(PersonalSpacePage, PersonalSpaceIndexPage)` adăugat la
query-ul de căutare.

### 8. Formulare de schimbare/resetare parolă simplificate
`{{ form.as_p }}` afișa automat regulile de validare Django (bullet-uri sub
câmpul de parolă nouă). Înlocuit cu buclă manuală peste câmpuri în
`password_change_form.html` și `password_reset_confirm.html` — păstrează
etichetele + erorile reale (parolă greșită, nepotrivire etc.), scoate doar
textul de ajutor generic.

### Ce s-a verificat efectiv (nu doar presupus)
Testat programatic, cu conturi de test create/șterse la fiecare pas (nu au
rămas în DB):
- Ana/Bogdan (grup Angajati): fiecare vede/publică doar propriul spațiu
  personal; Bogdan primește 403 la acces direct pe spațiul Anei.
- Permisiuni exacte confirmate: `can_add=True, can_publish=False` pe
  FAQ/Erori; `can_edit=True, can_publish=True` pe spațiul personal propriu.
- Zero acces la Documente confirmat (`has_perm('wagtaildocs.add_document')
  == False`) pentru Angajati; imagini/documente permise doar în colecțiile
  alocate (verificat cu `CollectionOwnershipPermissionPolicy`).
- Mihai/Elena (grup Moderators, fără superuser): editare+publicare
  confirmată pe un MenuPage oarecare (Suport), acces global la
  documente/imagini, DAR izolare pe spațiu personal identică cu Angajati.
- Carmen (cont nou, niciodată vizitat `/spatiul-meu/`): pagina personală se
  creează automat la prima intrare în admin, pe listarea Spații personale.
- Căutare globală: "Nicolae"/"Spatiul"/"personale" -> 0 rezultate din
  spații personale; "Suport"/"Proceduri"/"Vanzari" -> funcționează normal.
- Suita de teste existentă (`manage.py test home`, 4 teste) — trece după
  fiecare schimbare din sesiune.
- `git status` verificat la final — doar fișierele intenționate modificate,
  nimic altceva atins.

### Concluzie stabilitate (dev, la 2026-07-10)
Stabil pentru scenariul descris (~30 useri, 5-6 Administrator, restul
Angajati, opțional câțiva Moderators) — verificat programatic pe fiecare
regulă, nu doar configurat. Producția rămâne **neconfigurată intenționat**
(vezi lista de mai jos) — nu s-a atins nimic din infrastructura de deploy.

### Deferred — checklist producție (NEînceput, de reluat la aprobare deploy)
Descoperit într-o revizie separată a proiectului, nu rezolvat încă:
1. `DJANGO_SETTINGS_MODULE` nu e setat nicăieri în afara hardcodării pe
   `config.settings.dev` din `config/wsgi.py` — pe server real ar rula tot
   cu setări de dev (DEBUG=True, SECRET_KEY hardcodat, ALLOWED_HOSTS=["*"]).
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

## Cum continui pe altă mașină
1. `git pull`
2. `docker compose exec web python manage.py migrate` (aplică orice
   migrare nouă, inclusiv permisiunile din acest jurnal)
3. Citește secțiunea cea mai recentă de mai sus înainte să începi treabă
   nouă, ca să știi ce s-a decis deja și de ce.
4. La sfârșitul unei sesiuni de lucru importante, adaugă o secțiune nouă
   aici (nu rescrie ce există), cu același format: ce s-a schimbat, ce s-a
   verificat, ce rămâne.
