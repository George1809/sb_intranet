# Jurnal de lucru — SmartBill Intranet

Jurnal cronologic, pe sesiuni de lucru. Nu se rescrie istoricul — la fiecare
sesiune importantă (pe orice mașină), se adaugă o secțiune nouă la final. Vezi
`CLAUDE.md` pentru context general și `docs/RULES.md` pentru regulile stabile.

## 2026-07-09/10 (Linux, acasă) — prima construcție Erori/FAQ/Spațiu personal

- Adăugat `STREAM_BODY_BLOCKS` comun (StreamField refolosit de pagini
  manuale, erori, întrebări, spațiu personal).
- Modele noi: `ErrorIndexPage`/`ErrorReportPage`, `FAQIndexPage`/
  `FAQEntryPage` (cu bifă "Răspuns oferit"), `PersonalSpaceIndexPage`/
  `PersonalSpacePage`/`PersonalSpaceSection` (spațiu personal cu secțiuni
  multiple, pe principiul titlu/buton, cu rute proprii via
  `RoutablePageMixin`).
- Workflow de moderare nativ Wagtail (`Workflow`/`GroupApprovalTask`/
  `WorkflowPage`) pentru Erori/Întrebări — creat inițial printr-o comandă de
  management (`setup_support_access`), ulterior **înlocuită** de o migrare
  de date pe Windows (vezi sesiunea următoare) — comanda a rămas neștearsă,
  vezi nota de mai jos.
- `home/mail.py`: `ResilientSMTPEmailBackend` — Wagtail nu prindea
  `SMTPServerDisconnected` la notificările de workflow (doar
  `TimeoutError`/`ConnectionError`), ceea ce făcea toată acțiunea de
  aprobare să pice cu 500 dacă Yahoo întrerupea conexiunea. Testat cu eroarea
  simulată explicit — aprobarea reușește acum indiferent de starea SMTP.
- `home/wagtail_hooks.py` (inițial): ascunde meniul "Reports" din admin
  pentru non-superuseri (`construct_reports_menu`) + deconectare temporară a
  notificărilor de workflow pe email (semnale `task_submitted`/
  `workflow_submitted`/`workflow_rejected`/`workflow_approved`), la cererea
  userului, cât timp se testează manual fluxul de moderare. **De reactivat**
  când se configurează `WAGTAILADMIN_BASE_URL` cu domeniul real (altfel
  linkurile din notificări duc spre `example.com`).
- Setări email (`EMAIL_*`) citite din `.env` prin `python-dotenv` (era în
  `requirements.txt`, neactivat) — implicit consolă (safe), SMTP real dacă
  `EMAIL_HOST` e completat.
- Căutare globală extinsă să acopere și butoanele (documente/imagini/pagini
  manuale/linkuri), nu doar titlurile paginilor — plus `SEARCH_CONFIG:
  "romanian"` pe backend-ul Postgres (implicit era engleză, stemming greșit
  pe conținut românesc).
- Verificat: teste (4/4), `check`, migrații sincronizate, reset parolă
  end-to-end, aprobare cu SMTP picat (simulat).

## 2026-07-10 (Windows, la muncă)

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
  necesitat modele custom de Document/Imagine — respins, vezi
  `docs/RULES.md`). În loc, s-a creat arborele de **Collections** Wagtail
  (nativ, vizibil doar în admin, nu pe disc), oglindind structura de meniu:
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
  important, **cu izolare pe spațiul personal** (hook-urile sunt generice,
  se aplică oricărui non-superuser, nu doar grupului "Angajati"). E și grupul
  care aprobă workflow-ul de FAQ/Erori.
- **Angajati** (grup nou, creat prin migrarea `home/migrations/
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
  automat pagina personală a userului dacă nu exista încă.
- `before_edit_page` — a doua linie de apărare: blochează (403) accesul
  direct la editarea spațiului altcuiva, chiar dacă cineva ghicește URL-ul.

Important: aceste hook-uri sunt **generice**, se aplică oricărui
non-superuser, indiferent de grup.

### 6. `PersonalSpacePage.is_creatable = False`
Crash (`ValidationError: owner_user ... nu poate fi nul`) când cineva încerca
"Add child page" manual pe Spații personale. Fix cu un rând (`is_creatable =
False`) — Wagtail ascunde butonul ȘI blochează server-side accesul direct.

### 7. Scurgere de intimitate în căutarea globală
Căutarea globală (`search/views.py`) includea `PersonalSpacePage`/
`PersonalSpaceIndexPage` — deși "private" în admin, apăreau în căutarea de pe
site pentru orice user care căuta un cuvânt din titlu (ex. un nume). Reparat
cu `.not_type(PersonalSpacePage, PersonalSpaceIndexPage)`.

### 8. Formulare de schimbare/resetare parolă simplificate
`{{ form.as_p }}` afișa automat regulile de validare Django. Înlocuit cu
buclă manuală peste câmpuri — păstrează erorile reale, scoate textul de
ajutor generic.

### Ce s-a verificat efectiv pe Windows
Testat programatic (Ana/Bogdan, Mihai/Elena, Carmen — conturi de test, nu au
rămas în DB): izolare spațiu personal (403 pe acces direct la spațiul
altcuiva), permisiuni exacte pe FAQ/Erori vs spațiu personal, zero acces la
Documente pentru Angajati, izolare identică pentru Moderators fără superuser,
auto-creare pagină personală la prima intrare în admin, căutare globală fără
scurgere. Suita de teste (4/4) trece.

## 2026-07-10 (Linux, acasă) — verificare combinată după push/pull din Windows

Reevaluare completă după ce codul de pe Windows a fost adus aici prin
`git pull`. Verificat programatic, nu doar citit:

- **Teste (4/4), `check`, migrații** — toate curate (doar warning-urile
  preexistente treebeard, nelegate de cod).
- **Arbore de pagini** — confirmat: paginile Erori/Întrebări create inițial
  aici (aseară) au fost **mutate** (nu duplicate) sub noul meniu "Cazuri &
  Intrebari" creat pe Windows. Zero pierdere de conținut de test.
- **⚠️ Conflict găsit — workflow "orfan"**: `WorkflowPage.page` e
  `OneToOneField` (o pagină -> un singur workflow posibil). Workflow-ul creat
  aseară aici ("Aprobare Suport") a fost legat primul de paginile Erori/FAQ;
  migrarea de pe Windows a încercat să lege "Aprobare Angajati" de aceleași
  pagini, dar `get_or_create` a găsit deja legătura existentă și nu a
  schimbat nimic. Rezultat: **"Aprobare Angajati" există dar nu e folosit
  efectiv** — aprobările merg în continuare prin grupul vechi
  ("Moderatori Suport"), nu prin "Moderators" cum documentează sesiunea de
  pe Windows. Funcțional nu s-a stricat nimic (singurii moderatori sunt
  superuseri, care oricum au acces total), dar sunt acum **2 sisteme de
  grupuri paralele, redundante**:
  - Al meu (aseară): `Moderatori Suport`, `Acces limitat - Suport`,
    `Spatiu personal - <user>` (per user) + comanda
    `setup_support_access.py`.
  - Cel de pe Windows: `Angajati` (reutilizează `Moderators`, grup implicit
    Wagtail) + migrarea `0012_grup_angajati_permisiuni.py` + hook-urile de
    izolare din `wagtail_hooks.py`.
  
  **Recomandare, neexecutată încă** (de discutat cu userul): sistemul de pe
  Windows e mai complet (rezolvă izolarea spațiului personal între mai mulți
  useri limitați, ceea ce sistemul de aseară nu acoperea deloc). De
  consolidat pe acela, cu ștergerea grupurilor/workflow-ului/comenzii vechi
  și migrarea Violetei (userul de test creat aseară) în grupul `Angajati`.
- **⚠️ Gap real găsit — imagini/documente NU sunt izolate per user**: testat
  empiric (nu presupus) — doi useri diferiți din grupul `Angajati`, ambii cu
  drept pe Collection-ul comun "Spatii personale": user B **vede** imaginea
  încărcată de user A în selectorul de imagini (`choose`), confirmat din
  sursa Wagtail (`CollectionOwnershipPermissionPolicy.user_has_any_permission_for_instance`
  — acțiunea `choose` verifică doar Collection-ul, nu și
  `uploaded_by_user`). Izolarea de pagină (hook-urile) NU acoperă și
  biblioteca de imagini/documente. Fix posibil, nativ Wagtail (nediscutat/
  neexecutat încă): o sub-Collection per user sub "Spatii personale" (ca la
  pagini), cu permisiune scoped doar la userul respectiv — mai mult cod de
  configurare (migrare extinsă), nu cod custom nou.
- **CSS/fonturi** — verificat că fișierele de font chiar există pe disc și
  sunt servite corect (HTTP 200, dimensiuni normale), media query-ul de
  ecran scurt e prezent și scoped corect.
- **Cautare** — retestat: găsește conținut din body (nu doar titlu),
  respectă config-ul `romanian`, nu scurge titluri de spații personale.
- Documentația reorganizată: `input/input.md` (era exclus din git!) mutat în
  `docs/requirements.md` (acum urmărit de git), regulile stabile extrase în
  `docs/RULES.md`, jurnalul cronologic centralizat aici.

## 2026-07-10 (Linux, acasă) — consolidare finală permisiuni, 3 roluri

La cererea userului, cele 2 sisteme paralele găsite mai sus au fost unificate
într-unul singur, simplu și final:

- **Migrația `0014_consolidare_permisiuni.py`** (RunPython, ireversibilă
  intenționat la reverse): șterge grupurile vechi (`Moderatori Suport`,
  `Acces limitat - Suport`, orice `Spatiu personal - <user>`) și workflow-ul
  vechi (`Aprobare Suport`), apoi leagă corect `Aprobare Angajati` de
  paginile Erori/Întrebări (sloturile `WorkflowPage.page`, `OneToOneField`,
  erau deja ocupate de workflow-ul vechi — de-asta migrarea de pe Windows nu
  se legase efectiv, vezi găsirea de mai sus).
- **3 roluri finale**, verificate empiric (nu doar configurate):
  - **Administrator** — doar bifa Superuser, în niciun grup. Singurul cont:
    `george.nicolae86@yahoo.com`.
  - **Moderators** (grup implicit Wagtail, reutilizat neschimbat) — edit +
    publish peste tot (verificat pe un MenuPage), aprobă workflow-ul
    Angajaților, dar **nu** poate accesa spațiul personal al altcuiva (403
    confirmat direct pe URL, testat cu contul `...@gmail.com`, demotat din
    superuser și mutat aici).
  - **Angajati** — doar `anghel_violeta@ymail.com` acum. Poate adăuga (nu
    publica) pe Erori/Întrebări, publică direct propriul spațiu personal,
    nimic altceva.
- **Blocuri StreamField restrânse în spațiul personal**
  (`PERSONAL_SPACE_BLOCKS`, migrația `0013_alter_personalspacesection_body`):
  scoase `image`/`video_upload`/`document` — rămân doar `heading`,
  `paragraph`, `video` (link embed, nu fișier încărcat) și `link`. Motiv:
  acele 3 blocuri scoase aleg dintr-o Collection comună ("Spatii
  personale"), vizibilă la toți Angajații — un user ar fi văzut fișierele
  încărcate de un coleg. Simplificare aleasă în locul unei Collection
  separate per user (mai mult cod/configurare pentru un beneficiu mic la
  scara asta). Erori/Întrebări și paginile manuale rămân cu toate blocurile
  (conținut colaborativ, fără problemă de confidențialitate acolo).
- Ștearsă comanda `home/management/commands/setup_support_access.py`
  (înlocuită complet de migrația 0012 + 0014).
- **Verificat**: cele 4 teste trec, `check`/migrații curate, cele 3 roluri
  verificate direct (permisiuni + hook-uri de izolare + workflow legat
  corect), blocurile disponibile confirmate (`heading, paragraph, video,
  link` — exact 4, fără imagine/document).

### Corecție — blocuri repuse, ascuns meniul in loc

Userul a clarificat: nu voia eliminarea posibilității de a adăuga
imagini/documente în spațiul personal, ci doar ascunderea bibliotecii
generale de Images/Documents din meniul principal admin pentru Angajați (nu
are sens să răsfoiască toată colecția, unde ar vedea fișierele colegilor).

- **`PersonalSpaceSection.body`** — revenit la `STREAM_BODY_BLOCKS` complet
  (migrația `0015_alter_personalspacesection_body`) — imagine/document/
  video_upload disponibile din nou.
- **Hook nou `construct_main_menu`** (`hide_media_library_for_angajati`) —
  ascunde itemii "images"/"documents" din meniul principal admin, doar
  pentru membrii grupului `Angajati` (Moderators și Superuser văd meniul
  neschimbat). Notă importantă, comunicată userului: asta NU rezolvă complet
  scurgerea de confidențialitate — popup-ul de alegere a unei imagini, la
  adăugarea unui bloc în conținut, tot arată fișierele încărcate de colegi
  (permisiunea de bază pe Collection e neschimbată). E doar curățenie de UI
  (nu mai apare o cale evidentă de a răsfoi biblioteca), nu izolare reală.
  Dacă se dorește izolare reală mai târziu, varianta e o sub-Collection per
  user sub "Spatii personale" — discutată, neexecutată încă (aditivă, nu
  intră în conflict cu ce există acum).
- **Verificat direct** (`admin_menu.menu_items_for_request`, nu doar căutare
  de text în HTML, care dăduse fals-pozitiv): Angajat -> `['explorer',
  'help']`; Moderator -> `['documents', 'images', 'explorer', 'help']`;
  Superuser -> toate + `settings`/`reports`. Teste: 4/4.

### Bug reparat — crash la accesarea directă a "Spatii personale"
Userul a schimbat slug-ul paginii index (`PersonalSpaceIndexPage`) din admin
(din "Promovează") și a accesat noul URL direct (probabil "View live") —
`TemplateDoesNotExist: home/personal_space_index_page.html`. Pagina index
nu a avut niciodată template propriu, nefiind gândită să fie vizitată
direct (doar container ascuns). Fix: `serve()` suprascris pe
`PersonalSpaceIndexPage` să redirecționeze automat spre spațiul personal al
userului curent (aceeași logică ca `/spatiul-meu/`). Verificat: 302 către
spațiul propriu, teste 4/4.

### ✅ Reparat — gaură de confidențialitate pe randarea publică a spațiului personal
Userul a întrebat de ce eticheta nativă Wagtail de confidențialitate arată
"Vizibilă tuturor" pe "Spatii personale", deși ar trebui văzută doar de
proprietar. Investigat și confirmat empiric: **e o gaură reală, nu doar text
derutant**.

- Hook-urile din `wagtail_hooks.py` (`construct_explorer_page_queryset`,
  `before_edit_page`) izolează **doar admin-ul** (listare + editare) — NU și
  randarea publică a paginii pe site.
- Testat direct: Violeta (Angajat), logată, accesând pe frontend URL-ul
  spațiului personal al altcuiva (inclusiv al superuserului) doar
  ghicind/știind adresa -> `status: 200`, conținutul e citibil integral.
- Agravant: slug-ul e predictibil (`spatiul-personal-<id_user>`), deci
  URL-urile se pot ghici ușor prin încercare (id 1, 2, 3...).
- **Fix aplicat**: verificare `request.user == self.owner_user or
  request.user.is_superuser` în `PersonalSpacePage.get_context()` (acoperă
  ambele rute, `page_view` și `section_view`, fiindcă amândouă trec prin
  `get_context`), `raise Http404` altfel.
- **Verificat direct, toate cele 3 roluri**: Violeta (Angajat) -> spațiul
  altcuiva = 404, propriul spațiu = 200; Moderator (gmail) -> spațiul
  Violetei = 404; Superuser -> orice spațiu = 200 (vede tot, corect). Teste
  4/4.
- Important, clarificat cu userul: gaura NU era accesibilă prin navigare
  normală (`/spatiul-meu/` te duce mereu la propriul spațiu, verificat și
  înainte de fix) — era exploatabilă doar tastând/ghicind manual URL-ul
  altcuiva (slug previzibil, `spatiul-personal-<id>`). Nu risca expunere
  accidentală, dar tot merita reparat pentru conținut gândit ca privat.

Punctele deschise (linkuri RichText fără tab nou, izolare imagini/documente
per user, checklist producție) au fost mutate în `docs/TODO.md`, ca să nu se
piardă prin jurnal — acolo se adună tot ce a rămas de făcut, separat de
istoricul de-aici.

### Reparat — căutarea globală trata Erori/FAQ ca "secțiuni", nu ca butoane
Userul a observat (comparând cu screenshot-uri): în căutarea globală,
intrările individuale de Erori/Întrebări (`ErrorReportPage`/`FAQEntryPage`)
apăreau cu iconița generică de "pagină" și eticheta "Sectiune intranet" —
spre deosebire de butoanele din meniuri (document/imagine/link), care apar
corect cu iconița lor și "In <secțiune>". Cauza: sunt pagini Wagtail
adevărate (nu înregistrări separate ca butoanele din `MenuPage`), deci
`_page_results()` din `search/views.py` le trata generic.

- Fix: `_page_results()` verifică acum tipul specific al fiecărui rezultat
  (`base_result.specific`) — dacă e `ErrorReportPage`/`FAQEntryPage`,
  primește `kind="error"`/`"faq"` și subtitlul devine numele secțiunii
  părinte, nu mai generic "Sectiune intranet".
- `search.html` — adăugate cele 2 iconițe (triunghi de avertizare pentru
  error, cerc cu semn de întrebare pentru faq), identice cu cele deja
  folosite pe paginile de listare Erori/Întrebări — nimic nou vizual, doar
  refolosire.
- Verificat direct: "Erori comune" (secțiunea însăși) → `page` / "Sectiune
  intranet"; intrările individuale → `error` / "In Erori comune". Teste
  4/4.

## 2026-07-12 (Linux, acasă) — categorii Erori/Întrebări, redesign CSS

### Fix — selector confuz la "Add child page"
`ErrorIndexPage`/`FAQIndexPage` aveau `parent_page_types` incluzând orice
`MenuPage`, fără `max_count` — apărea un selector de tip pagină și pe
subsecțiuni fără legătură (ex. "test1"). Restrâns `parent_page_types` la
`["home.HomePage"]` + `max_count = 1` pe ambele, scos din `subpage_types`
al lui `MenuPage`. Verificat cu `can_create_at()`: Home → încă oferă
tipurile; orice subsecțiune → doar `MenuPage`. Fără migrare (atribute
Python, nu schema DB).

### Adăugat — categorii la Erori comune și Întrebări
Structură nouă, cerută de user: `Erori comune`/`Întrebări` → categorie →
intrare (înainte era direct index → intrare).

- Modele noi `ErrorCategoryPage`/`FAQCategoryPage` (migrații 0016-0017),
  câte 4 categorii identice la fiecare: Gestiune-Facturare Cloud,
  SmartBill POS, Conta, Integrari (redenumite ulterior din "SmartBill
  Gestiune/Facturare Cloud"/"SmartBill Conta" — migrația 0018 — și cu `/`
  → `-` în ultima, migrația 0019, ca să nu se confunde cu separatorul din
  breadcrumb).
- Pagina "Cazuri & Întrebări" arată acum direct, pe o singură pagină, 2
  coloane (Erori/Întrebări) cu categoriile fiecăreia — fără click
  suplimentar prin index — via context special în `MenuPage.get_context()`
  (`is_cazuri_intrebari`, detectat după slug, ca la `is_quick_links`).
- **Permisiuni Angajați — varianta A**: mutate de pe `ErrorIndexPage`/
  `FAQIndexPage` (unde aveau add/change pe tot subarborele) pe fiecare
  categorie în parte. Efect: pot adăuga intrări în categorii existente,
  NU pot crea categorii noi (fiindcă n-au `add_page` la nivelul index-ului
  unde s-ar crea o categorie). Verificat empiric cu Violeta: `can_add_subpage()`
  True pe categorie, False pe index; `can_publish()` False (merge la
  aprobare, ca înainte).
- Discutat cu userul și clarificat: mecanismul de aprobare ("Submit for
  moderation") e 100% default Wagtail (add fără publish + workflow activ),
  nu ține de tipul paginii — ce a cerut model dedicat a fost forma
  conținutului (StreamField + câmpuri proprii), nu fluxul de aprobare.
- Templates noi: `error_category_page.html`/`faq_category_page.html`
  (listează intrările, identic cu ce făceau înainte index-urile);
  `error_index_page.html`/`faq_index_page.html` rescrise să arate grila de
  categorii; `includes/category_icon.html` (icon comun, simplificat la
  cererea userului la iconița-dosar unică, nu diferită per categorie, ca
  să nu fie haotic).
- Găsit temporar 4 intrări vechi de test rămase orfane direct sub index
  (create înainte să existe categorii) — nu apăreau în noua listare pe
  categorii, deși rămâneau live/accesibile pe URL. Userul le-a șters
  manual din admin.

### CSS — redesign in 3 variante, discutate și testate cu userul
Sesiune lungă de iterații, ghidată de feedback vizual direct (userul se
uita pe monitor și descria ce vede).

- **Varianta 1** = starea comisă la `f51f789` (paleta multicoloră
  originală: verde + lime/galben + mint/teal + albastru, decor generos).
  Salvată ca reper numit în memoria persistentă a Claude Code (nu doar în
  sesiune), cu instrucțiuni de revenire (`git checkout f51f789 -- ...`).
- **Varianta 2** = trecere pe un singur accent (verde) peste tot — scoase
  culorile decorative lime/mint/albastru din gradient-uri, iconițe pe tip,
  păstrat roșu strict la erori/logout și galben la FAQ "în așteptare"
  (semnal funcțional, nu decor). Nu s-a comis niciodată ca atare — salvată
  separat, ca fișier, în memoria Claude Code (userul a refuzat explicit un
  commit-checkpoint pentru ea), recuperabilă prin copiere peste fișierul
  curent.
- **Varianta 3** (păstrată, aplicată acum) = plecând de la Varianta 2:
  mai mult alb (fundaluri simplificate), iconițe cu senzație de adâncime
  (gradient + highlight + umbră, nu mai plate), carduri/butoane cu
  border/umbră vizibile din stare normală (nu doar la hover), hover mai
  pronunțat. Apoi, pe parcursul mai multor runde de feedback vizual:
  formele decorative (bulă ovală + arc pe hero, cercuri pe carduri) au
  fost înlocuite, testate și ajustate de câteva ori — starea finală
  acceptată: hero cu o nuanță verde difuză mai pronunțată (fără formă cu
  contur), cardurile/butoanele clicabile (secțiuni, categorii, tile-uri de
  meniu, butoane de resurse) toate cu același semicerc verde discret în
  colț, avatarul din hero cu inelul conic verde estompat (55% opacitate) și
  spațiul alb intern original restaurat exact (tehnica `padding-box`/
  `border-box` cu inset 12px, așa cum era, nu o versiune "reparată" care
  schimba proporțiile).
- Fix separat: umbra de sub navbar (sticky header) era prea mare/opacă
  (36px blur, 24% opacitate) — redusă (10px blur, 14%).
- Fix: iconița de întrebare (cerc cu semn de întrebare) de la Erori/
  Întrebări nu era centrată corect — path SVG desenat de mână, ușor
  asimetric. Înlocuit peste tot (coloana din "Cazuri & Întrebări",
  `faq_category_page.html`, `search.html`) cu iconița standard Material
  Design "help", verificată ca fiind simetrică.

### Alte ajustări mici
- Separator vizual (linie) pe pagina de schimbare parolă, între câmpul de
  parolă veche și cele două de parolă nouă/confirmare.
- Avatar fallback: folosește iconița de favicon (`img/favi.png`) în loc de
  `sb_mark_grey.svg`, peste tot unde un user nu are poză de profil setată
  (navbar + hero) — o singură schimbare în `context_processors.py`,
  aplicată automat în ambele locuri.
- Label-urile din formularul de login/parolă aliniate la greutatea de font
  700 (erau rămase la 900 din varianta veche).

Verificat la final: migrări curate, teste 4/4, toate cele 43 de pagini
live randează OK (superuser), Violeta (Angajat) OK pe toate rutele
relevante, anonim redirect corect la login, CSS static 200.
