# Uputstvo za upotrebu aplikacije Taxi Zoran

Ovo uputstvo objašnjava svaku opciju u aplikaciji i kako se koristi. Aplikacija služi za evidenciju vožnji, praćenje troškova (gorivo, servis, ostali troškovi), i pravljenje izveštaja za knjigovodstvo.

---

## 1. Prvo pokretanje i zaključavanje otiskom prsta

Kad prvi put otvoriš app, pojaviće se **Početni ekran** direktno (zaključavanje je isključeno po difoltu).

Ako u Podešavanjima uključiš **Sigurnost (otisak prsta)**, sledeći put kad pokreneš app prvo ćeš videti ekran sa zahtevom da prisloniš prst na senzor. Bez uspešnog otiska ne možeš dalje.

- Ako telefon nema čitač otiska, ili nijedan otisak nije registrovan u sistemskim podešavanjima telefona, app te **automatski propušta dalje** i samo te obaveštava zašto — nema opasnosti da se trajno zaključaš van app-a.
- Zaključavanje se proverava samo pri **pokretanju app-a** (hladnom startu), ne pri svakom povratku iz pozadine — tako da te ne prekida usred aktivne vožnje ako, na primer, primiš poziv.
- Uključuje/isključuje se u **Podešavanja → Sigurnost (otisak prsta)**.

---

## 2. Početni ekran

Šest glavnih prečica:

| Dugme | Šta radi |
|---|---|
| **GPS vožnja (auto)** | Otvara automatsko praćenje vožnje preko GPS-a (poglavlje 3.1) |
| **Početak vožnje (ručno)** | Otvara Kalkulator za ručni unos vožnje (poglavlje 3.2) |
| **Istorija vožnji** | Otvara Evidenciju — spisak svih vožnji sa pretragom (poglavlje 3.3) |
| **Izveštaj** | Dnevni/nedeljni/mesečni pregled zarade (poglavlje 4.1) |
| **Profil vozača** | Lični podaci i podaci o vozilu (poglavlje 5.5) |
| **Podešavanja** | Svi ostali meniji aplikacije (poglavlje 5) |

---

## 3. Beleženje vožnji

### 3.1 GPS vožnja (automatski unos) — najčešća opcija

Ovo je glavni način unosa vožnje dok voziš:

1. **(Opciono)** Pre nego što klikneš "Počni vožnju", možeš uneti krajnju adresu u polje "Krajnja adresa" — ako je uneseš, čim klikneš Start, odmah će se otvoriti Google navigacija korak-po-korak ka toj adresi. Ako ostaviš prazno, i dalje sve radi normalno — samo bez automatskog otvaranja navigacije.
2. Klikneš **POČNI VOŽNJU**. App traži dozvolu za lokaciju ako je prvi put, zatim počinje da meri kilometražu u realnom vremenu na ekranu.
3. Ekran u toku vožnje prikazuje: adresu polaska, pređene kilometre, trajanje vožnje i trenutnu cenu (obračunatu uživo).
4. Kad stigneš, klikneš **ZAVRŠI VOŽNJU**. App sam pronalazi tvoju trenutnu adresu (reverse geocoding) i čuva vožnju u Evidenciju.

**Bitne napomene:**
- GPS vožnja koristi samo dve tarife: **Osnovnu** ili **Noćnu** — koja od njih važi zavisi isključivo od prekidača u **Podešavanja → Noćna tarifa** (nije automatski po satu). Za Vikend ili Aerodromski transfer koristi ručni unos (Kalkulator).
- App filtrira lošu GPS preciznost (ignoriše tačke lošije od 50m preciznosti, mikro-skokove ispod 10m i nerealne skokove brzine preko 180 km/h) da kilometraža ne bi bila lažno naduvana.
- Ako iz nekog razloga GPS ne uspe da izmeri kilometražu, na ekranu za završetak vožnje postoji polje za ručni unos km kao rezerva.

### 3.2 Kalkulator (ručni unos vožnje)

Za vožnje koje ne pratiš uživo preko GPS-a, ili kad želiš tarifu koju GPS vožnja ne podržava (Vikend, Aerodromski transfer):

1. Izaberi tarifu iz padajućeg menija (Osnovna / Noćna / Vikend / Aerodromski transfer).
2. Unesi kilometražu — cena se odmah preračunava i prikazuje ispod (start taksa + km × cena po km).
3. Adresa polaska, adresa dolaska i napomena su opcioni.
4. Klik na **Sačuvaj vožnju**.

Ako je uključena Noćna tarifa (poglavlje 5.2), ekran automatski predlaže Noćnu tarifu pri otvaranju — i dalje možeš ručno da je promeniš za tu konkretnu vožnju.

### 3.3 Evidencija (istorija vožnji)

Prikazuje sve sačuvane vožnje, najnovije prve. Za svaku vožnju vidi se datum, vreme početka/kraja, kilometraža, tarifa, adrese i cena.

**Pretraga** — možeš kombinovati:
- tekst (pretražuje adrese i napomenu),
- period (datum od / datum do, format GGGG-MM-DD),
- opseg cene (cena od / cena do).

Klik na **Pretraži** ispisuje i zbir (broj vožnji, ukupno km, ukupna zarada) za rezultate pretrage. **Resetuj** vraća pun spisak.

Svaka vožnja ima dva dugmeta:
- **Izmeni** — otvara Kalkulator popunjen tim podacima; kad sačuvaš, stara vožnja se zamenjuje izmenjenom.
- **Obriši** — trajno briše tu vožnju (bez potvrde, pa pazi).

---

## 4. Izveštaji i statistika

### 4.1 Izveštaj zarade

Tri kartice sa zbirovima:
- **Danas** — spisak svih vožnji danas (početak-kraj, cena) + ukupno.
- **Ova nedelja** — zbirna zarada za tekuću nedelju.
- **Ovaj mesec** — zbirna zarada za tekući mesec.

Odavde ide dugme **Izvoz PDF** ka ekranu za izvoz izveštaja (poglavlje 4.3).

### 4.2 Grafikon zarade

Vizuelni prikaz kroz vreme, sa opcijama:
- **Period**: Dnevni / Nedeljni / Mesečni prikaz.
- **Prikaz**: Zarada ili Kilometri (bira se šta grafikon crta).
- Strelice **< >** pomeraju se kroz prethodne/naredne periode.
- Klik na tačku u grafikonu prikazuje tačan iznos za taj dan/nedelju/mesec.
- Ispod grafikona: dodatne statistike (npr. prosek, poređenje sa prethodnim periodom) i, kad ima podataka, kombinovan pregled potrošnje goriva i servisa za taj period.

Pristupa se preko **Podešavanja → Grafik zarade**.

### 4.3 Izvoz izveštaja (PDF / CSV za Excel)

Ekran **Izveštaj → Izvoz PDF** (ili Podešavanja → Nedeljni/Mesečni izveštaj → Izvoz PDF).

1. Izaberi vrstu perioda: Dnevno, Nedeljno, Mesečno, Polugodišnje ili Godišnje.
2. Unesi period u traženom formatu (menja se u zavisnosti od izbora — app ti pokazuje tačan primer).
3. Dva dugmeta za izvoz:

**Izvezi PDF** — pravi PDF fajl za štampu/pregled, sa:
- podacima o vozaču u zaglavlju,
- tabelom servisa u periodu,
- tabelom ostalih troškova,
- potrošnjom goriva (l/100km između uzastopnih sipanja) i svim unosima goriva,
- tabelom svih vožnji,
- zbirnim redom na kraju: broj vožnji, ukupno km, bruto zarada i **neto** (zarada minus gorivo minus servisi minus ostali troškovi).

**Izvezi CSV (Excel)** — pravi jedan CSV fajl gde su vožnje, gorivo, servisi i troškovi pomešani u JEDNU tabelu (kolone: Datum, Tip, Opis, Prihod, Rashod, Napomena), sortirano po datumu — lakše za knjigovođu da otvori u Excel-u i sam sabira/filtrira. Fajl je zapisan tako da Excel ispravno prikazuje slova č, ć, š, đ, ž.

Oba fajla se čuvaju u **Preuzimanja/TaksiApp** na telefonu (isti folder kao backup). Potrebna je dozvola "pristup svim fajlovima" — ako je nemaš, app te upozori i uputi u Podešavanja → Backup podataka.

---

## 5. Podešavanja

### 5.1 Cene / Tarife

Ovde se menjaju cene po kilometru za sve četiri tarife, plus start taksa:
- Start taksa (RSD)
- Osnovna (07-22h)
- Noćna (22-07h)
- Vikend
- Aerodromski transfer

Klik na **Sačuvaj cene** primenjuje ih na SVE naredne vožnje (ne menja retroaktivno već sačuvane vožnje).

### 5.2 Noćna tarifa (prekidač)

Jedan prekidač: kad je uključen, i Kalkulator i GPS vožnja automatski koriste Noćnu tarifu (i dalje možeš ručno promeniti tarifu za pojedinačnu vožnju u Kalkulatoru). Ne uključuje se sam po satu — ti ga uključuješ i isključuješ ručno kad počinje/prestaje tvoja noćna smena.

### 5.3 Gorivo

Evidencija sipanja goriva:
- Vrsta (Benzin / TNG)
- Količina (litara)
- Cena
- **Kilometraža na pumpi** (opciono, ali VAŽNO — bez nje se ne može izračunati potrošnja niti radi podsetnik za servis)
- Napomena

Na vrhu ekrana vidi se ukupno potrošeno na gorivo (posebno benzin, posebno TNG). Potrošnja u l/100km se automatski računa u pozadini iz razlike kilometraže između dva uzastopna sipanja koja imaju upisanu kilometražu — vidi se u PDF izveštaju i grafikonu.

### 5.4 Servis vozila

Evidencija servisa (zamena ulja, kočnice, itd.) — vrsta, cena, kilometraža, napomena.

**Podsetnik za servis**: postaviš interval (npr. "na svakih 10000 km"), a app sam prati koliko je pređeno od poslednjeg servisa — poredeći kilometražu poslednjeg servisa sa najnovijom kilometražom upisanom kod **Goriva** (ne sa ukupnim km iz vožnji). Kartica na vrhu menja boju:
- **zeleno** — sve OK,
- **žuto** — ostalo je manje od 20% intervala,
- **crveno** — vreme je za servis (interval pređen).

Ako nema još dovoljno podataka (bar jedan servis SA kilometražom i bar jedno gorivo SA kilometražom sa pumpe), kartica samo kaže da nema dovoljno podataka.

### 5.5 Ostali troškovi

Za sve što ne spada u gorivo/servis: Parking, Putarina, Pranje, Ostalo — cena i napomena. Ovi troškovi ulaze u NETO izračun u PDF izveštaju.

### 5.6 Profil vozača

Lični podaci (ime, telefon, licenca, tablice, vozilo) koji se prikazuju u zaglavlju PDF izveštaja, plus:
- **Datum isteka registracije**
- **Datum isteka osiguranja**

Kartica na dnu ekrana prati oba datuma i menja boju:
- sivo — datum nije unet,
- zeleno — više od 30 dana do isteka,
- žuto — 30 dana ili manje do isteka,
- crveno — već isteklo (piše koliko dana kasni).

### 5.7 Navigacija

Nezavisan ekran za brzo otvaranje Google navigacije ka bilo kojoj adresi — unesi adresu i klikni "Otvori navigaciju". Automatski kreće korak-po-korak od tvoje trenutne GPS pozicije (nije potrebno ručno kliktati "Kreni" u Google Maps-u).

### 5.8 Google API

Opcionalno polje za Google Geocoding API ključ. Ako ga ne uneseš, app i dalje radi normalno — koristi besplatan OpenStreetMap servis za pronalaženje adresa. Google-ov servis je samo precizniji u pojedinim slučajevima. Ključ se pravi na console.cloud.google.com (Geocoding API).

### 5.9 Valuta

Bira se samo kako se cene **prikazuju** u app-u — u pozadini se sve uvek računa i čuva u RSD (dinarima), bez obzira na ovaj izbor:
- **Prikazuj u RSD** ili **Prikazuj u EUR** (dugmad).
- Kurs se automatski osvežava jednom dnevno (prvi put kad tog dana otvoriš app). Dugme **Osveži kurs sada** za ručno osvežavanje ako npr. juče nije bilo interneta.

### 5.10 Backup podataka

Čuva SVE podatke (vožnje, gorivo, servisi, troškovi, profil vozača) u jedan fajl van same aplikacije, u **Preuzimanja/TaksiApp** — ostaje na telefonu i posle brisanja/reinstalacije app-a.

- **Odobri pristup fajlovima** — daje app-u Android dozvolu da piše u taj javni folder (traži se jednom).
- App sam pravi svež backup jednom dnevno pri pokretanju, tiho, bez poruke.
- **Sačuvaj backup sada** — ručni backup kad god poželiš.
- **Vrati podatke iz backupa** — učitava sve podatke iz backup fajla (koristi se pri promeni telefona ili posle reinstalacije).
- **Podeli backup (Drive, WhatsApp...)** — otvara sistemski meni za deljenje da pošalješ backup fajl sebi na mejl, Google Drive, WhatsApp itd. — koristan način da backup ne zavisi samo od samog telefona.

**Pri promeni telefona:** napravi backup na starom telefonu → prebaci fajl (WhatsApp/Drive/USB) u isti folder na novom → instaliraj app na novom → klikni "Vrati podatke".

### 5.11 Sigurnost (otisak prsta)

Uključuje/isključuje zaključavanje app-a otiskom prsta pri pokretanju — detaljno objašnjeno u poglavlju 1. Ekran ti kaže i da li tvoj telefon uopšte ima registrovan otisak.

---

## 6. Poziv / Dispečer

Ova stavka u meniju trenutno prikazuje samo "Uskoro..." — funkcionalnost još nije implementirana.

---

## 7. Najčešći problemi

| Problem | Rešenje |
|---|---|
| GPS ne pokazuje kilometražu | Proveri da li si dao dozvolu za lokaciju (Podešavanja telefona → Aplikacije → Taksi App → Dozvole → Lokacija → Dozvoli) i da li je GPS uključen na telefonu |
| Ne mogu da izvezem PDF/CSV | Idi u Podešavanja → Backup podataka → "Odobri pristup fajlovima" |
| Ne radi otisak prsta | Proveri da li telefon uopšte ima čitač otiska i da li je otisak registrovan u sistemskim podešavanjima telefona — bez toga app te automatski propušta dalje |
| Podsetnik za servis kaže "nema dovoljno podataka" | Potreban je bar jedan servis SA upisanom kilometražom i bar jedno gorivo SA upisanom kilometražom sa pumpe |
| Cene se ne poklapaju sa novim tarifama | Nove cene važe samo za vožnje UNETE POSLE izmene — ne menjaju retroaktivno već sačuvane vožnje |

---

*Uputstvo odgovara verziji aplikacije sa GitHub repozitorijuma taxizoran1967-byte/taxizoran1967, stanje na dan generisanja ovog dokumenta.*
