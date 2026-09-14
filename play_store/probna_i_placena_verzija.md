# Probna verzija (7 dana) + placena verzija - analiza i predlog

## 1. Da li ovo vec postoji u aplikaciji?

**NE.** Pregledao sam ceo kod (main.py i svih 18 ekrana) i trazio sve
sto ima veze sa: license, trial/probna verzija, billing/kupovina,
aktivacija, premium, pretplata. Jedini pogodak je bio polje "broj
licence" u profilu vozaca - to je taksisticka (radna) licenca, nema
veze sa placanjem aplikacije.

Zakljucak: aplikacija trenutno radi punom funkcionalnoscu, zauvek,
besplatno, bez ikakvog ogranicenja. Sistem probne/placene verzije
mora se napraviti od nule.

## 2. Sta treba dodati da bi radilo

Potrebne su tri stvari:

1. **Merenje vremena od prve instalacije** - kada korisnik prvi put
   pokrene app, sacuvati taj datum lokalno. Svaki sledeci put,
   uporediti sa danasnjim datumom - ako je proslo vise od 7 dana i
   aplikacija nije aktivirana, ukljuciti ograniceni rezim.

2. **Ogranicen rezim rada** - definisati sta tacno radi, a sta ne radi
   posle isteka probnog perioda (npr. i dalje se mogu gledati stari
   podaci, ali se ne mogu dodavati nove voznje; ili se GPS voznja i
   PDF izvoz zakljucaju, a rucni unos ostaje). Ovo je odluka koju
   TREBA DA DONESES TI - koje funkcije su "mamac" za probnu verziju, a
   koje su vredne placanja.

3. **Sistem aktivacije pune verzije** - da korisnik posle placanja
   dobije trajan pristup. Detalji ispod.

## 3. Kako napraviti sistem aktivacije - dve realne opcije

### Opcija A: Google Play Billing (kupovina kroz sam Play Store)
Korisnik klikne "Otkljucaj punu verziju" u aplikaciji, Google Play
otvori svoj plati-jednom-prozor, naplati karticu, i aplikacija dobije
potvrdu direktno od Google-a.

Prednosti:
- Google vodi racuna o placanju, priznanicama, povracaju novca (refund)
- Korisnik vec ima karticu vezanu za Play Store nalog - jednostavnije
  za njega
- Najveci deo korisnika ovo ocekuje i veruje mu

Mane:
- Google uzima proviziju (obicno 15% za male prihode, ~30% posle
  praga)
- Tehnicki slozenije da se ugradi u OVU aplikaciju - Kivy/buildozer
  nema zvanicnu, gotovu podrsku za Google Play Billing biblioteku.
  Trazi se ili poseban "recipe" (dodatak) za python-for-android, ili
  pisanje Java/Kotlin mosta (bridge) koji Python kod poziva preko
  pyjnius biblioteke (koja se vec koristi u projektu za druge Android
  funkcije, sto je dobra vest - infrastruktura delimicno postoji).

### Opcija B: Sopstveni aktivacioni kljuc
Ti (ili neki tvoj sistem) generises kod (npr. "TAXI-8F2K-91AB"),
korisnik ga unese u aplikaciju, aplikacija proveri da li je ispravan i
otkljuca se trajno.

Prednosti:
- Tehnicki jednostavnije da se ugradi u postojecu Kivy aplikaciju -
  samo jedan novi ekran sa poljem za unos koda
- Nema provizije Google-u na samu proveru koda (ali i dalje treba
  nacin da naplatis - videti ispod)

Mane:
- **Placanje mora da se resi odvojeno** - kljuc sam po sebi ne
  naplacuje nista; treba ili rucno slanje kljuca posle uplate (npr.
  bankovni racun, PayPal), ili sopstvena veza sa placanjem (Stripe i
  slicno) - dodatan rad
- **Slabija zastita od zloupotrebe** ako se radi jednostavno - jedan
  kljuc se moze podeliti sa drugim ljudima ili se moze naci u
  aplikaciji "reverse engineering"-om ako se ne uradi pazljivo (npr.
  kljuc treba da bude vezan za konkretan telefon/uredjaj, ne univerzalan
  za sve)
- Nema automatskog refund/pritužbe sistema - to bi ti rucno resavao

## 4. Moja preporuka

Za ozbiljno, dugorocno objavljivanje na Google Play, **Google Play
Billing (opcija A)** je ispravniji izbor - to ocekuje i Google i
korisnici, i most preko pyjnius je izvodljiv (vec se koristi slican
pristup u projektu za android permisije). Slozeniji je za napraviti,
ali se pravi jednom.

Ako zelis brze i jednostavnije resenje za pocetak (npr. da odmah
pocnes da naplacujes dok se Play Billing ne ugradi), aktivacioni
kljuc (opcija B) moze da posluzi kao privremeno resenje, uz svest da
je slabije zasticen.

## 5. Sledeci korak

Ovo je SAMO analiza - nista od ovoga nije programirano niti dirano u
aplikaciji, kako je i trazeno. Kada odlucis koju opciju zelis (A ili
B), i koje tacno funkcije treba da budu ogranicene tokom probnog
perioda, javi mi - napravicu detaljan plan izmena PRE nego sto bilo
sta menjam u kodu.
