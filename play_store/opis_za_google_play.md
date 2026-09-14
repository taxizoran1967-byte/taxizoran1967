# Google Play - tekst za stranicu aplikacije

## Naziv aplikacije (max 30 karaktera)
Downtown Taxi

(Napomena: unutar same aplikacije, na pocetnom ekranu, sada pise
"DOWNTOWN TAXI" logo. Android sistem ce ispod ikonice na telefonu
i dalje prikazivati "Taksi App" (ime iz buildozer.spec) dok se to
ne promeni i napravi novi build - videti napomenu na kraju ovog
fajla.)

## Kratak opis (max 80 karaktera)
Evidencija voznji, GPS, gorivo i zarada za taksiste - sve na jednom mestu

(broj karaktera: 74)

## Kategorija
Predlog: **Business** (Posao / Poslovanje)
Alternativa: Maps & Navigation (manje odgovara, aplikacija nije prvenstveno
navigacija vec evidencija/racunovodstvo za vozaca)

## Tagovi / kljucne reci (za ASO - optimizaciju pretrage)
taksi, taxi, vozac, evidencija voznji, gps prevoz, dnevni izvestaj,
gorivo potrosnja, servis vozila, taksi zarada, putni nalog

---

## Dugacak opis (max 4000 karaktera)

Downtown Taxi je aplikacija napravljena za taksiste i vozace koji zele
jednostavnu i preciznu evidenciju svojih voznji, troskova i zarade -
sve na srpskom jeziku, bez potrebe za internet nalogom ili placanjem
pretplate za osnovno koriscenje.

ŠTA APLIKACIJA RADI

Downtown Taxi prati vase voznje (automatski preko GPS-a ili rucnim
unosom), racuna cenu prema vasim tarifama, evidentira troskove
(gorivo, servis, ostalo) i pravi dnevne, nedeljne i mesecne izvestaje
o zaradi - sa mogucnoscu izvoza u PDF ili Excel (CSV) formatu.

GLAVNE FUNKCIJE

- GPS voznja (automatski) - prati rutu u realnom vremenu, sam racuna
  predjenu kilometrazu i cenu voznje
- Rucni unos voznje - kalkulator za voznje koje ne pratite GPS-om
- Istorija voznji - pretraga po datumu, tekstu ili ceni, izmena i
  brisanje unosa
- Cetiri tipa tarifa - osnovna, nocna, vikend i aerodromski transfer,
  svaka sa sopstvenom cenom po kilometru i start taksom, podesivo u
  aplikaciji bez ponovnog instaliranja
- Dnevni, nedeljni i mesecni izvestaj zarade, sa grafikonom
- Izvoz izvestaja u PDF i CSV (Excel) formatu, spremno za stampu
- Evidencija goriva (benzin/TNG) - unos rucno ili skeniranjem racuna
  (OCR prepoznavanje teksta sa slike racuna), automatski racuna
  potrosnju litara na 100 km
- Evidencija servisa vozila sa podsetnicima po predjenim kilometrima
  (zeleni/zuti/crveni status koliko je servis blizu)
- Ostali troskovi (parking, putarina, pranje vozila...)
- Imenik dispecera sa smenama, za brzo pozivanje
- Brza navigacija - jednim dodirom otvara Google Maps do odredista
- Prikaz u RSD ili EUR, kurs se automatski osvezava
- Profil vozaca - licni podaci, registracija i osiguranje sa
  podsetnicima o isteku
- Zakljucavanje aplikacije otiskom prsta (biometrijska zastita)
- Rucni backup i vracanje svih podataka na telefonu

KOME JE NAMENJENA

Taksistima, vozacima privatnih prevoznika i svima koji zele uredan,
tacan pregled koliko su vozili, potrosili i zaradili - bez rucnog
vodjenja beleznice ili Excel tabele.

PREDNOSTI

- Sve na srpskom jeziku
- Svi podaci ostaju na vasem telefonu - nema obaveznog naloga ni
  prijave
- Radi i bez interneta za osnovnu evidenciju (internet je potreban
  samo za GPS adresu, kurs valute i skeniranje racuna)
- Pregledni izvestaji spremni za knjigovodju ili licnu evidenciju
- Podsetnici za servis i registraciju, da vam nista ne promakne

---

## NAPOMENA (za vlasnika aplikacije, ne za Google Play)

Reseno: naziv aplikacije je promenjen u buildozer.spec
(`title = Downtown Taxi`) i napravljen je nov AAB build sa tim nazivom -
sada se svuda zove isto: na Play Store stranici, ispod ikonice na
telefonu i na logu unutar aplikacije.

Napomena: `package.name` (taksiapp) i `package.domain` (org.licno) NISU
menjani - to je tehnicki identitet aplikacije (applicationId), i ne
sme da se menja jer bi to za Google Play bila "sasvim nova" aplikacija.
Promenjen je samo naziv koji korisnik vidi.
