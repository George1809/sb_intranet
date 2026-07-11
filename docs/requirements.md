# Proiect de tip Intranet

Se doreste sa fie o aplicatie sau un intranet care contine informatii utile pentru desfasurarea activitatii in companie, lucrand la SmartBill, soft de facturare, gestiune, contabilitate si soft e vanzare de tip POS, pentru emiterea de bonuri fiscale. 
Vreau sa documentez cat mai bine si sa structurez pe meniuri informatiile si sa le adaug in intranet cat mai usor si rapid posibil pe parcursul actualizarilor. 
Vor fi informatii de tip release notes, link-uri rapide pe care le folosim poate, documentat erori si cazuri uzuale/comune, documentat tool-urile pe care le folosim, proceduri si informatii pe departamente (Suport, Vanzari, Conta) si cam tot ce se tine intr-un intranet
Pe parcurs vom dezvolta, ca imi doresc sa implementem un sistem de training, pe stilul udemy de exemplu, dar implicit cu ce are wagtail inclus, sa ramana simplu din punct de vedere operational si usor de actualizat din admin si construit de acolo si placut vizual si usor de parcurs. Totodata, in cazul sectiunii de training sa fie sectiune de exercitii cu completare de catre nou angajat si cu trimitere pe mail al unui set de exercitii pe categorie (suport, vanzari, conta sau POS de exemplu). Apoi trainerul si managerul sa vada notificare ca s-au terminat exercitiile si printr-un link sa acceseze exercitiile completate, sa se poata oferi review si cumva o nota si sa se poata face usor din cadrul intranetului, unde vor lucra new joinerii si cu trainer si manager. 

### Ce se doreste cu acest proiect: 

- sa fie o aplicatie care va fi folosita de aproximativ 30 de colegi, din care doar 5 sau 6 colegi vor avea drept de editare si acces admin
- in prima varianta si in prima faza, sa fie o varianta de intranet stabila si pregatita sa fie urcata pe un server real si cu 2 medii de dezvoltare (pc de serviciu cu windows si pc de acasa cu linux); dar, momentan nu umblam la docker, vom umbla doar in momentul in care se va urca real pe server si voi mentiona atunci
- ca UI/design, sa fie folosit doar CSS, doar in cazul in care e ceva supercomplex cand voi cere, sa imi mentionezi si vedem daca punem JS
- sa fie cat mai aerisit, codul curat si foarte stabil si secure
- aplicatia la fel, sa fie aerisita, elementele ordonate bine si css stabil si sa arate bine
- sa se foloseasca cat mai mult tot ce are wagtail inclus sa fie ok operational si usor de lucrat in admin si de adaugat informatii
- am zis sus la proiect de tip intranet cam cum ar vrea sa fie si sa fie o logica generala pe butoanele adaugate, de tip meniu principal -> submeniu -> lista de butoane cu diferite tipuri de fisiere si informatii afisate la accesarea unui buton, butoane ce se adauga si se construiesc pe parcurs in functie de informatii. 
- unele meniuri principale sau chiar subsectiuni, pot primi logica diferita dupa accesare, sa putem construi asta cand e nevoie si voi specifica. De exemplu, cum este trainingul, va avea o logica diferita la accesarea meniului principal. Apoi mai avem subsectiunile case de marcat si flags, din meniul principal suport, cele 2 vor avea la fel, logica diferita fiecare, nu vor avea la accesare lista cu butoane. 

### Ce punem la punct in prima parte a proiectului/aplicatiei, tinand cont de aspectele mentionate deja: 

- suita de pagini pe baza instructiunilor oferite si in chat prompt, cu meniu principal, unele puse in dashboard sa arate ok ca UI
- avem meniul principal -> meniul secundar -> in fiecare meniu secundar sa se poata adauga butoane accesibile, care pot contine: un pdf-uri care se deschide in alt tab la accesare, imagini care se deschid in alt tab la accesare buton, pagini manuale construite din admin si alte fisiere uzuale ce se folosesc de regula. 
- doar cand sunt exceptii sa se construiasca diferit si voi mentiona asta
- CSS-ul si aplicatia sa fie cat mai stabila din punct de vedere operational, mentenanta, accesare date si usor de continuat de cineva, daca eu nu voi mai putea vea grija si actualiza de exemplu, sa se pastreze totul cat mai simplu.
- tot ce se construieste ulterior, sa se tina cont de tema culorilor, structuri si sa se acompanieze totul ok. 
<!-- - apoi, la fiecare user, tot asa, cu ce are wagtail inclus, sa aiba la profil, deja vei vedea, spatiul lui personal unde isi poate popula informatii. Se pote construi acolo de catre user, sa isi adauge el pagini manuale cumva, butoane cu informatii si documente si pagini manuale, cum faci si din admin? e greu de facut? Adica se poate folosi optim cu wagtail inclus?  -->
- login-ul sa fie stabil si ok pentru numarul de useri specificat
- restul de ~24 colegi (fara drept de editare) au doar acces frontend (fara `/admin/`). Doar cei 5-6 admin au acces total peste tot, restul doar in interfata aplicatiei din browser.
- conturile se creeaza manual din admin si isi vor reseta ei parolele.
- puse la punct cautarea globala, stabil si cu ce are wagtail inclus, pe tot intranetul + buton de cautare si pe fiecare subsectiune accesata, unde sunt butoane si unde va cauta doar in subsectiunea cu butoane accesata.
- release notes se trateaza ca orice alt tip de continut (pagina manuala/document), in regula generale de meniu, sub meniu si lista cu butoane?
- despre backup mediu productie se va discuta in momentul in care se va urca pe server.
- **Training (faza ulterioara)**: de clarificat cand ajungem acolo - cine trimite exercitiile (automat la creare cont sau manual), ce format au (formular Wagtail vs upload fisier), cum se notifica trainerul/managerul (email, dashboard intern), ce nivel de "nota"/review (text liber vs scor). (aici revin cu instructiuni cat mai clare intr-o noua sectiune)
- **Date sensibile / GDPR**: sectiunea de training va stoca nume, avatare, exercitii completate si note ale angajatilor noi - hostat intern, dar de vazut daca exista vreo politica interna de retentie/acces la aceste date. (aici la fel, voi discuta cand va fi cazul si voi prezenta aplicatia)



<!-- parole posibiel, doar pentru mine, tu ignora
smartbillgeorge
SMARTBILLGEORGE
smartbillvioleta
 -->