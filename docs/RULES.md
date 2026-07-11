# Reguli de lucru — SmartBill Intranet

Reguli stabile, valabile pe termen lung, stabilite explicit cu userul pe
parcursul dezvoltării. Nu se schimbă de la o sesiune la alta — dacă apare o
regulă nouă sau una veche se schimbă, se actualizează direct aici (nu se
păstrează istoric de reguli vechi, pentru asta există `CHANGELOG.md`).

- **Zero JS** pe partea de site — doar CSS + Django/Wagtail template-uri.
  Dacă apare vreodată un caz suficient de complex încât CSS-ul singur nu
  ajunge, se menționează explicit userului și se decide împreună dacă se
  adaugă JS — nu se adaugă niciodată implicit.
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
- Userul lucrează pe **2 mașini** (Linux acasă, Windows la muncă), fiecare cu
  propriul Docker/Postgres local (bazele de date NU se sincronizează prin
  git — doar codul). După orice `git pull` care aduce migrări noi, trebuie
  rulat manual `docker compose exec web python manage.py migrate`.
- Cerințele complete originale sunt în `docs/requirements.md` — se citește
  acolo "ce" s-a cerut; regulile de aici sunt "cum" se lucrează. `CHANGELOG.md` e "ce s-a făcut și verificat" pe parcurs.
