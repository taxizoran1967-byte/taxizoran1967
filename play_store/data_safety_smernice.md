# Data Safety - smernice za popunjavanje u Google Play Console

Google Play "Data safety" sekcija se NE popunjava fajlom - popunjava se
kroz formu (upitnik) direktno u Play Console, kada budes objavljivao
aplikaciju. Ovde su TACNI odgovori, na osnovu stvarnog koda aplikacije
(ne pretpostavke), da ih samo prekucas u formu.

## Da li aplikacija prikuplja ili deli korisnicke podatke?
DA (lokacija i fotografija se salju spoljasnjim servisima radi
funkcionalnosti - vidi ispod).

## Tipovi podataka

### Lokacija (Location)
- Precizna lokacija (GPS): DA, prikuplja se
- Svrha: funkcionalnost aplikacije (GPS pracenje voznje, navigacija)
- Da li se deli sa trecim stranama: DA - salje se Google Maps API i
  OpenStreetMap (Nominatim) servisima radi pretvaranja koordinata u
  adresu i prikaza rute
- Da li korisnik moze da odbije: DA (GPS voznja je opcionalna funkcija,
  postoji i rucni unos)
- Da li se prenosi sifrovano (enkriptovano): DA (HTTPS)
- Da li korisnik moze da trazi brisanje: DA (lokalni podaci se brisu
  brisanjem aplikacije ili kroz opciju u aplikaciji)

### Fotografije (Photos)
- Prikuplja se: DA (samo ako korisnik koristi "Skeniraj racun (OCR)")
- Svrha: funkcionalnost aplikacije (automatsko citanje racuna za
  gorivo)
- Deli se sa trecim stranama: DA - salje se servisu OCR.space radi
  prepoznavanja teksta
- Opciono: DA (moze se i rucno uneti bez skeniranja)
- Prenosi se sifrovano: DA (HTTPS)

### Licni podaci (Personal info)
- Ime, telefon i slicno (profil vozaca): DA, ali se cuva SAMO lokalno
  na uredjaju, ne salje se nigde
- Deli se sa trecim stranama: NE

### Finansijski podaci (Financial info)
- Cene voznji, zarada, troskovi: DA, ali se cuva SAMO lokalno na
  uredjaju
- Deli se sa trecim stranama: NE

### App activity / App info and performance
- Ne prikuplja se (nema analitike, nema crash reportinga, nema
  reklamnih SDK-ova u projektu)

## Da li se podaci brisu na zahtev korisnika?
DA - brisanjem aplikacije ili unutar "Backup podataka" ekrana.

## Da li je prenos podataka sifrovan?
DA - svi spoljasnji pozivi idu preko HTTPS (potvrdjeno u kodu -
urllib sa SSL kontekstom).

## Sigurnosna praksa
Aplikacija ne trazi nalog niti lozinku. Zakljucavanje otiskom prsta je
opciono i koristi Android-ov ugradjeni biometrijski sistem (aplikacija
nema pristup samom otisku, samo dobija DA/NE odgovor od sistema).

---

NAPOMENA: Ovo je priprema na osnovu pregleda koda. Kada popunjavas
formu u Play Console, Google ponekad menja pitanja/kategorije - ako
neko pitanje ne prepoznajes tacno, javi mi tekst pitanja pa ti kazem
tacno sta da izabeeš na osnovu koda.
